"""Avisos de RF-11 (patrón Observer del SRS, sección 4).

El flujo de estados solo dice *qué pasó* (`al_alta`, `al_cambiar_estado`, ...); este módulo decide *a quién*
avisar según la tabla de RF-11 y deja, en la misma transacción, el aviso en el sistema (`aviso_sistema`) y el
correo pendiente (`envio_correo`). El correo se envía después, fuera de la transacción
(`procesar_correos`): si el servicio falla, el cambio que lo originó ya quedó guardado (RF-11-AC-4) y se
reintenta hasta 3 veces con 10 minutos entre intentos; al tercer fallo queda «Fallido».
"""

import logging
from datetime import timedelta
from typing import Iterable, Optional

from . import config, reloj
from .correo import CorreoNoEnviado, servicio
from .util import fecha_legible, new_id, now_utc

log = logging.getLogger("reportaya.avisos")

ESTADO_LEGIBLE = {
    "Reportado": "Reportado",
    "Asignado": "Asignado",
    "EnProceso": "En proceso",
    "Terminado": "Terminado",
    "Cerrado": "Cerrado",
    "Cancelado": "Cancelado",
    "Unido": "Unido",
}
PAGADOR_LEGIBLE = {"Condominio": "el condominio", "Condomino": "el condómino (propietario)"}


# ----------------------------------------------------------------- destinatarios
def _usuario(db, uid: Optional[str]):
    if not uid:
        return None
    return db.execute("SELECT id, nombre, correo, estado_cuenta FROM usuario WHERE id=?", (uid,)).fetchone()


def administracion(db) -> list:
    return db.execute("""SELECT id, nombre, correo FROM usuario WHERE rol='Administracion' AND estado_cuenta='Activa'
                         ORDER BY rowid""").fetchall()


def _propietario_a_avisar(db, r) -> Optional[str]:
    """Correo del propietario de la unidad cuando no es el reportante (RD-05).

    En áreas comunes, ninguno (RF-11-AC-3)."""
    u = db.execute("SELECT propietario_correo FROM unidad WHERE ubicacion_id=?", (r["ubicacion_id"],)).fetchone()
    if not u:
        return None
    rep = _usuario(db, r["reportante_id"])
    if rep and rep["correo"].lower() == u["propietario_correo"].lower():
        return None
    return u["propietario_correo"]


# ----------------------------------------------------------------- registro
def _registrar(
    db,
    folio: str,
    evento: str,
    mensaje: str,
    asunto: str,
    usuarios: Iterable = (),
    correos_sin_cuenta: Iterable[str] = (),
) -> None:
    """Un aviso en el sistema y un correo por cada usuario con cuenta; solo correo para quien no tiene cuenta."""
    ahora = now_utc()
    vistos = set()
    for u in usuarios:
        if u is None or u["id"] in vistos:
            continue
        vistos.add(u["id"])
        aid = new_id()
        db.execute(
            "INSERT INTO aviso (id, tipo, reporte_folio, evento, fecha) VALUES (?, 'Sistema', ?, ?, ?)",
            (aid, folio, evento, ahora),
        )
        db.execute(
            "INSERT INTO aviso_sistema (aviso_id, destinatario_usuario_id, mensaje) VALUES (?,?,?)",
            (aid, u["id"], mensaje),
        )
        _correo(db, folio, evento, u["correo"], asunto, mensaje, ahora)
    for c in correos_sin_cuenta:
        if c and c.lower() not in {x.lower() for x in vistos}:
            vistos.add(c)
            _correo(db, folio, evento, c, asunto, mensaje, ahora)


def _correo(db, folio, evento, destinatario, asunto, cuerpo, ahora):
    aid = new_id()
    db.execute(
        "INSERT INTO aviso (id, tipo, reporte_folio, evento, fecha) VALUES (?, 'Correo', ?, ?, ?)",
        (aid, folio, evento, ahora),
    )
    db.execute(
        "INSERT INTO envio_correo (aviso_id, destinatario, asunto, cuerpo) VALUES (?,?,?,?)",
        (aid, destinatario, asunto, cuerpo),
    )


def _sin_cuenta_a_administracion(db, r, que: str) -> None:
    """RF-11-AC-8: si el reportante no tiene canal digital, la Administración lo comunica manualmente."""
    contacto = f" ({r['contacto_referencia']})" if r["contacto_referencia"] else ""
    _registrar(
        db,
        r["folio"],
        "ComunicarManualmente",
        f"{r['folio']}: {que}. El reportante «{r['nombre_referencia']}»{contacto} no tiene cuenta: "
        f"comuníqueselo manualmente.",
        f"ReportaYa {r['folio']}: comunicar al reportante",
        administracion(db),
    )


# ----------------------------------------------------------------- eventos de la tabla de RF-11
def al_alta(db, r) -> None:
    """Alta de un reporte: residente reportante (si lo hay) y Administración (reporte nuevo). RF-11-AC-1."""
    aviso = fecha_legible(r["fecha_aviso"])
    rep = _usuario(db, r["reportante_id"])
    if rep:
        _registrar(
            db,
            r["folio"],
            "AltaReporte",
            f"Registramos su reporte {r['folio']} con fecha de aviso {aviso}.",
            f"ReportaYa: reporte {r['folio']} registrado",
            [rep],
        )
    _registrar(
        db,
        r["folio"],
        "ReporteNuevo",
        f"Reporte nuevo {r['folio']} (aviso {aviso}).",
        f"ReportaYa: reporte nuevo {r['folio']}",
        administracion(db),
    )
    if r["posible_duplicado_de"]:  # RF-17-AC-1
        _registrar(
            db,
            r["folio"],
            "PosibleDuplicado",
            f"{r['folio']} quedó marcado como posible duplicado de {r['posible_duplicado_de']}.",
            f"ReportaYa: posible duplicado {r['folio']}",
            administracion(db),
        )


def al_cambiar_estado(db, r, estado_nuevo: str, detalle: str = "", plazo_hasta: Optional[str] = None) -> None:
    """`Asignado`, `Terminado`, `Cerrado`, `Cancelado`, `Unido` o reapertura: residente reportante y, en
    unidades, el propietario cuando no es el reportante (solo correo, RF-11-AC-2). `EnProceso` no avisa al
    residente (RF-11-AC-7), salvo que sea una reapertura."""
    fecha = fecha_legible(now_utc())
    estado = ESTADO_LEGIBLE[estado_nuevo]
    mensaje = f"Su reporte {r['folio']} cambió a «{estado}» el {fecha}."
    if detalle:
        mensaje += f" {detalle}"
    if estado_nuevo == "Terminado" and plazo_hasta and r["reportante_id"]:  # RF-11-AC-9
        mensaje += f" Puede responder «Ya quedó» o «Sigue fallando» hasta el {fecha_legible(plazo_hasta)}."
    asunto = f"ReportaYa: {r['folio']} ahora está «{estado}»"
    rep = _usuario(db, r["reportante_id"])
    if rep:
        _registrar(db, r["folio"], f"Estado:{estado_nuevo}", mensaje, asunto, [rep])
    elif r["nombre_referencia"]:
        _sin_cuenta_a_administracion(db, r, f"cambió a «{estado}»")
    prop = _propietario_a_avisar(db, r)
    if prop:
        costo = f" Responsable del costo: {PAGADOR_LEGIBLE[r['responsable_costo']]}." if r["responsable_costo"] else ""
        _registrar(
            db,
            r["folio"],
            f"Estado:{estado_nuevo}",
            f"El reporte {r['folio']} de su unidad cambió a «{estado}» el {fecha}.{costo}",
            asunto,
            correos_sin_cuenta=[prop],
        )


def al_asignar_responsable(db, r) -> None:
    """Asignación o reclasificación de responsable: ese usuario de Mantenimiento, si tiene cuenta (RF-11-AC-5).
    Un proveedor sin acceso no recibe nada (RF-06-AC-10)."""
    u = _usuario(db, r["responsable_usuario_id"])
    if u:
        _registrar(
            db,
            r["folio"],
            "Asignacion",
            f"Se le asignó el reporte {r['folio']} con prioridad «{r['prioridad']}».",
            f"ReportaYa: se le asignó {r['folio']} ({r['prioridad']})",
            [u],
        )


def al_residente(db, r, evento: str, mensaje: str) -> None:
    """Detención, reanudación o reclasificación de la responsabilidad: residente reportante (RF-18-AC-5, RF-06-AC-9)."""
    rep = _usuario(db, r["reportante_id"])
    if rep:
        _registrar(db, r["folio"], evento, mensaje, f"ReportaYa: novedades de {r['folio']}", [rep])


def al_cancelar_residente(db, r, motivo: str) -> None:
    """Cancelación por el residente: Administración y responsable asignado (RF-11-AC-6)."""
    destinatarios = list(administracion(db)) + [_usuario(db, r["responsable_usuario_id"])]
    _registrar(
        db,
        r["folio"],
        "CanceladoPorResidente",
        f"El residente canceló {r['folio']}. Motivo: «{motivo}».",
        f"ReportaYa: {r['folio']} cancelado por el residente",
        destinatarios,
    )


def al_cambiar_visita(db, r) -> None:
    """Cambio de la fecha programada de visita (RF-15-AC-2): los mismos que en «cambio de estado»."""
    texto = (
        f"La visita para {r['folio']} quedó programada para el {fecha_legible(r['fecha_visita'])}."
        if r["fecha_visita"]
        else f"Se canceló la visita programada de {r['folio']}."
    )
    asunto = f"ReportaYa: visita de {r['folio']}"
    rep = _usuario(db, r["reportante_id"])
    if rep:
        _registrar(db, r["folio"], "Visita", texto, asunto, [rep])
    prop = _propietario_a_avisar(db, r)
    if prop:
        _registrar(db, r["folio"], "Visita", texto, asunto, correos_sin_cuenta=[prop])


# ----------------------------------------------------------------- envío y reintentos
def procesar_correos(db) -> int:
    """Envía los correos pendientes cuyo siguiente intento ya toca. Devuelve cuántos intentó.
    Cada intento se guarda en su propia transacción corta; un fallo nunca revierte nada más."""
    ahora = reloj.ahora()
    limite = reloj.a_texto(ahora - timedelta(minutes=config.CORREO_REINTENTO_MINUTOS))
    filas = db.execute(
        """SELECT * FROM envio_correo WHERE estado='Pendiente' AND intentos < 3
                          AND (fecha_ultimo_intento IS NULL OR fecha_ultimo_intento <= ?)
                          ORDER BY rowid""",
        (limite,),
    ).fetchall()
    for f in filas:
        intentos = f["intentos"] + 1
        try:
            servicio().enviar(f["destinatario"], f["asunto"], f["cuerpo"])
            estado = "Enviado"
        except CorreoNoEnviado as e:
            log.warning("Correo a %s no enviado (intento %s/3): %s", f["destinatario"], intentos, e)
            estado = "Fallido" if intentos >= 3 else "Pendiente"
        db.execute(
            "UPDATE envio_correo SET estado=?, intentos=?, fecha_ultimo_intento=? WHERE aviso_id=?",
            (estado, intentos, reloj.a_texto(ahora), f["aviso_id"]),
        )
    return len(filas)


def correo_directo(destinatario: str, asunto: str, cuerpo: str) -> bool:
    """Correos que no pertenecen a un reporte (enlaces de activación y recuperación, RF-14)."""
    try:
        servicio().enviar(destinatario, asunto, cuerpo)
        return True
    except CorreoNoEnviado as e:
        log.warning("Correo a %s no enviado: %s", destinatario, e)
        return False


# ----------------------------------------------------------------- reportes estancados (RF-22)
def revisar_estancados(db) -> int:
    """Avisa a la Administración, una sola vez hasta que cambie de estado, de cada reporte que lleva más del
    umbral de su prioridad sin cambiar de estado. No cuentan los detenidos, los `Terminado` (esperan al
    residente) ni los estados finales. Devuelve cuántos avisos generó."""
    from .reglas import parametro

    umbral = {p: parametro(db, f"umbralEstancamiento{p}Horas") for p in ("Urgente", "Normal", "Menor")}
    ahora = reloj.ahora()
    filas = db.execute("""SELECT r.*, (SELECT MAX(e.fecha) FROM entrada_historial e JOIN cambio_estado c ON
        c.entrada_id = e.id
                                       WHERE e.reporte_folio = r.folio) AS ultimo_cambio
                          FROM reporte r WHERE r.estado IN ('Reportado','Asignado','EnProceso')
                          AND NOT EXISTS (SELECT 1 FROM detencion d WHERE d.reporte_folio = r.folio AND d.fecha_fin
                              IS NULL)""").fetchall()
    n = 0
    for r in filas:
        prioridad = r["prioridad"] or r["prioridad_sugerida"]
        desde = reloj.de_texto(r["ultimo_cambio"])
        if ahora - desde <= timedelta(hours=umbral[prioridad]):
            continue
        if db.execute(
            "SELECT 1 FROM aviso WHERE reporte_folio=? AND evento='Estancado' AND fecha >= ?",
            (r["folio"], r["ultimo_cambio"]),
        ).fetchone():
            continue  # RF-22-AC-2: una sola vez
        horas = int((ahora - desde).total_seconds() // 3600)
        db.execute("BEGIN")
        try:
            _registrar(
                db,
                r["folio"],
                "Estancado",
                f"{r['folio']} («{prioridad}») lleva {horas} h en «{ESTADO_LEGIBLE[r['estado']]}» sin moverse.",
                f"ReportaYa: {r['folio']} no se ha movido",
                administracion(db),
            )
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise
        n += 1
    return n


def ciclo_de_mantenimiento(db) -> None:
    """Tarea periódica: alertas de estancamiento y reintentos de correo."""
    revisar_estancados(db)
    procesar_correos(db)
