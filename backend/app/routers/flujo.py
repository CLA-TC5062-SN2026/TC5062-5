"""Transiciones de estado del reporte (RF-06, RF-07, RF-08, RF-09, RF-17, RF-19, RF-25).

Cada transición es un subrecurso creado con POST (convención del contrato): assignments, cycles,
completions, resident-responses, closures, cancellations, reopenings y merges. Orden de errores (SRS 3.0):
401 sin sesión → 404 no visible → 403 sin permiso → 409 transición no permitida → 422 validación.
Cada transición, su historial y sus avisos se guardan en una sola transacción; los correos salen después.
"""

import json
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, File, Form, Header, Path, Response, UploadFile

from .. import config, reloj, schemas as S
from .. import notificaciones as N
from .. import visibilidad as V
from ..db import get_db, tx
from ..reglas import (
    abrir_ciclo,
    ciclo_actual,
    es_responsable,
    exigir_gestion,
    exigir_transicion,
    mas_horas,
    obtener_reporte,
    parametro,
    reclasificacion,
    registrar_cambio_estado,
)
from ..security import ADMIN, MANT, RES, UsuarioSesion, actor
from ..serial import responsable_out
from ..util import (
    FOLIO_RE,
    conflicto,
    fecha_legible,
    now_utc,
    out_dt,
    peticion_invalida,
    prohibido,
    responder,
    validacion,
    verificar_if_match,
)
from .reportes import (
    MAX_FOTOS_POR_ETAPA,
    _resolver_ubicacion,
    despachar,
    detalle_para,
    dentro_de_plazo_de_reapertura,
    deshacer_archivos,
    guardar_adjuntos,
    validar_archivos,
    visible,
)

router = APIRouter()
FolioP = Path(..., pattern=FOLIO_RE)
RESPONSABILIDAD_LEGIBLE = {"Comun": "Común", "Privada": "Privada", "PorDeterminar": "Por determinar"}


def hoy() -> date:
    """Fecha de hoy en la zona del condominio (reloj controlable, RNF-10)."""
    return reloj.ahora().astimezone(config.TIMEZONE).date()


def _responder_detalle(db, quien, folio, status=200, location=None):
    return responder(detalle_para(db, quien, folio), status, location, etag=status == 200)


def _resolver_responsable(db, responsable_id: str) -> tuple[Optional[str], Optional[str], str]:
    """(usuario de Mantenimiento, proveedor sin acceso, nombre). Uno de los dos, nunca ambos (RF-06)."""
    u = db.execute(
        """SELECT u.id, u.nombre FROM usuario u JOIN usuario_mantenimiento m ON m.usuario_id = u.id
                      WHERE u.id=? AND u.estado_cuenta <> 'Desactivada'""",
        (responsable_id,),
    ).fetchone()
    if u:
        return u["id"], None, u["nombre"]
    p = db.execute("SELECT id, nombre FROM proveedor_sin_acceso WHERE id=? AND activo=1", (responsable_id,)).fetchone()
    if p:
        return None, p["id"], p["nombre"]
    raise validacion("responsableId", "El responsable no existe o está desactivado")


def _nombre_responsable(db, r) -> Optional[str]:
    ref = responsable_out(db, r)
    return ref["nombre"] if ref else None


def _etiqueta_ubicacion(db, ubicacion_id) -> Optional[str]:
    if not ubicacion_id:
        return None
    return db.execute("SELECT etiqueta FROM v_ubicacion WHERE id=?", (ubicacion_id,)).fetchone()["etiqueta"]


def _actor_de_mantenimiento(db, quien: UsuarioSesion, r) -> Optional[str]:
    """Mantenimiento asignado o Administración. Para un proveedor sin acceso registra la Administración en su
    nombre (RF-07-AC-10); devuelve el id del proveedor para el historial."""
    if quien.rol == MANT:
        if not es_responsable(r, quien.id):  # no visible para él: 404 (RF-07-AC-4); exigir_visible ya lo cubrió
            raise prohibido()
        return None
    if quien.rol != ADMIN:
        raise prohibido()
    return r["responsable_proveedor_id"]


# ------------------------------------------------------------------ asignación (RF-06)
@router.post("/reports/{folio}/assignments")
def assign_report(
    folio: str = FolioP, body: Any = Body(...), db=Depends(get_db), quien: UsuarioSesion = Depends(actor)
):
    r = visible(db, quien, folio)
    exigir_gestion(db, quien)
    exigir_transicion(r, "Asignado")
    d = S.parsear(S.AssignRequest, body)
    if d.prioridad is None:
        raise validacion("prioridad", "La prioridad es obligatoria")  # RF-06-AC-3
    if not d.responsableId:
        raise validacion("responsableId", "El responsable es obligatorio")
    usuario_id, proveedor_id, nombre = _resolver_responsable(db, d.responsableId)
    origen = _resolver_ubicacion(db, d.ubicacionOrigen, "ubicacionOrigen")[0] if d.ubicacionOrigen else None
    responsabilidad = d.responsabilidad or "PorDeterminar"
    with tx(db):
        db.execute(
            """UPDATE reporte SET estado='Asignado', prioridad=?, responsable_usuario_id=?, responsable_proveedor_id=?,
                      ubicacion_origen_id=COALESCE(?, ubicacion_origen_id), responsabilidad=?,
                      responsable_costo=COALESCE(?, responsable_costo) WHERE folio=?""",
            (d.prioridad, usuario_id, proveedor_id, origen, responsabilidad, d.responsableCosto, folio),
        )
        registrar_cambio_estado(db, folio, r["estado"], "Asignado", quien.id)
        # Cada dato de la asignación queda con valor anterior y nuevo (RF-06).
        reclasificacion(db, folio, quien.id, "prioridad", r["prioridad_sugerida"] + " (sugerida)", d.prioridad)
        reclasificacion(db, folio, quien.id, "responsable", None, nombre)
        if origen:
            reclasificacion(
                db,
                folio,
                quien.id,
                "ubicacionOrigen",
                _etiqueta_ubicacion(db, r["ubicacion_id"]),
                _etiqueta_ubicacion(db, origen),
            )
        if d.responsabilidad and d.responsabilidad != r["responsabilidad"]:
            reclasificacion(
                db,
                folio,
                quien.id,
                "responsabilidad",
                RESPONSABILIDAD_LEGIBLE[r["responsabilidad"]],
                RESPONSABILIDAD_LEGIBLE[responsabilidad],
            )
        if d.responsableCosto:
            reclasificacion(db, folio, quien.id, "responsableCosto", r["responsable_costo"], d.responsableCosto)
        nuevo = obtener_reporte(db, folio)
        N.al_asignar_responsable(db, nuevo)  # RF-11-AC-5 / RF-06-AC-10
        N.al_cambiar_estado(db, nuevo, "Asignado")  # RF-11-AC-2, AC-8
    despachar(db)
    return _responder_detalle(db, quien, folio, 201, f"/reports/{folio}/assignments/1")


# ------------------------------------------------------------------ reclasificación (RF-06)
# Campo del cuerpo -> (columna, cómo se muestra el valor en el historial). RF-06-AC-8 y RD-10 para la prioridad.
def _tal_cual(valor):
    return valor


RECLASIFICACION_SIMPLE = {
    "prioridad": ("prioridad", _tal_cual),
    "responsabilidad": ("responsabilidad", RESPONSABILIDAD_LEGIBLE.get),
    "responsableCosto": ("responsable_costo", _tal_cual),
}


def _campos_de_reclasificacion(r, d) -> set:
    campos = d.model_fields_set
    if not campos:
        raise validacion("cuerpo", "Indique al menos un dato para reclasificar")
    for c in campos:
        if getattr(d, c) is None:
            raise validacion(c, "No admite null")
    if "responsableId" in campos and r["estado"] not in ("Asignado", "EnProceso"):
        raise conflicto("El responsable solo se cambia en Asignado o En proceso")
    return campos


def _cambiar_responsable(db, folio, quien, r, responsable_id) -> bool:
    usuario_id, proveedor_id, nombre = _resolver_responsable(db, responsable_id)
    if (usuario_id, proveedor_id) == (r["responsable_usuario_id"], r["responsable_proveedor_id"]):
        return False
    anterior = _nombre_responsable(db, r)
    db.execute(
        "UPDATE reporte SET responsable_usuario_id=?, responsable_proveedor_id=? WHERE folio=?",
        (usuario_id, proveedor_id, folio),
    )
    reclasificacion(db, folio, quien.id, "responsable", anterior, nombre)  # RF-06-AC-4
    return True


def _cambiar_origen(db, folio, quien, r, ubicacion) -> None:
    origen = _resolver_ubicacion(db, ubicacion, "ubicacionOrigen")[0]
    if origen == r["ubicacion_origen_id"]:
        return
    db.execute("UPDATE reporte SET ubicacion_origen_id=? WHERE folio=?", (origen, folio))
    anterior = _etiqueta_ubicacion(db, r["ubicacion_origen_id"] or r["ubicacion_id"])
    reclasificacion(db, folio, quien.id, "ubicacionOrigen", anterior, _etiqueta_ubicacion(db, origen))


@router.patch("/reports/{folio}/classification")
def reclassify_report(
    folio: str = FolioP,
    body: Any = Body(...),
    if_match: str = Header(...),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    exigir_gestion(db, quien)
    verificar_if_match(if_match, detalle_para(db, quien, folio))
    if r["estado"] not in ("Asignado", "EnProceso", "Terminado"):
        raise conflicto("Transición no permitida")
    d = S.parsear(S.ReclassifyRequest, body)
    campos = _campos_de_reclasificacion(r, d)
    cambiados = set()
    with tx(db):
        for campo in ("prioridad", "responsableId", "ubicacionOrigen", "responsabilidad", "responsableCosto"):
            if campo not in campos:
                continue
            valor = getattr(d, campo)
            if campo == "responsableId":
                if _cambiar_responsable(db, folio, quien, r, valor):
                    cambiados.add(campo)
            elif campo == "ubicacionOrigen":
                _cambiar_origen(db, folio, quien, r, valor)
            elif valor != r[RECLASIFICACION_SIMPLE[campo][0]]:
                columna, legible = RECLASIFICACION_SIMPLE[campo]
                db.execute(f"UPDATE reporte SET {columna}=? WHERE folio=?", (valor, folio))
                reclasificacion(db, folio, quien.id, campo, legible(r[columna]), legible(valor))
                cambiados.add(campo)
        nuevo = obtener_reporte(db, folio)
        if "responsableId" in cambiados:
            N.al_asignar_responsable(db, nuevo)
        if "responsabilidad" in cambiados:  # RF-06-AC-9
            legible = RESPONSABILIDAD_LEGIBLE[d.responsabilidad]
            N.al_residente(db, nuevo, "Responsabilidad", f"La responsabilidad de {folio} quedó como «{legible}».")
    despachar(db)
    return _responder_detalle(db, quien, folio)


# ------------------------------------------------------------------ inicio de la atención (RF-07)
@router.post("/reports/{folio}/cycles")
def start_cycle(
    folio: str = FolioP,
    body: Any = Body(default={}),
    idempotency_key: Optional[str] = Header(default=None),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    en_nombre_de = _actor_de_mantenimiento(db, quien, r)
    if r["estado"] != "Asignado":
        raise conflicto("Transición no permitida")
    d = S.parsear(S.StartRequest, body)
    if d.comentario is not None and len(d.comentario) > 1000:
        raise validacion("comentario", "Máximo 1,000 caracteres")
    with tx(db):
        db.execute("UPDATE reporte SET estado='EnProceso' WHERE folio=?", (folio,))
        n = abrir_ciclo(db, folio)
        registrar_cambio_estado(db, folio, "Asignado", "EnProceso", quien.id, d.comentario, en_nombre_de)
        # RF-11-AC-7: el paso a En proceso no avisa al residente.
    return _responder_detalle(db, quien, folio, 201, f"/reports/{folio}/cycles/{n}")


# ------------------------------------------------------------------ terminado con evidencia (RF-08)
def _leer_completion(datos: Optional[str]) -> S.CompletionData:
    if not datos:
        return S.CompletionData()
    try:
        return S.parsear(S.CompletionData, json.loads(datos))
    except json.JSONDecodeError as exc:
        raise peticion_invalida("La parte `datos` no es un JSON válido") from exc


def _validar_textos_de_terminado(d) -> None:
    for campo in ("notaTrabajo", "pendientes"):
        valor = getattr(d, campo)
        if valor is not None and len(valor) > 1000:
            raise validacion(campo, "Máximo 1,000 caracteres")


def _garantia(texto: Optional[str]) -> Optional[date]:
    """RF-25: fecha de vencimiento de la garantía, opcional y nunca pasada."""
    if texto is None:
        return None
    try:
        garantia = date.fromisoformat(texto)
    except ValueError:
        raise validacion("garantiaVencimiento", "Fecha no válida (use AAAA-MM-DD)")
    if garantia < hoy():
        raise validacion("garantiaVencimiento", "La fecha de vencimiento no puede ser pasada")
    return garantia


def _excepcion_sin_evidencia(quien: UsuarioSesion, r, d) -> tuple:
    """RD-09: solo un proveedor sin acceso, registrado por la Administración, puede terminar sin fotos."""
    if quien.rol != ADMIN or not r["responsable_proveedor_id"]:
        raise validacion("fotos", "Adjunte al menos una foto del trabajo terminado")  # RF-08-AC-2, AC-6
    if not d.justificacionSinEvidencia or not d.justificacionSinEvidencia.strip():
        raise validacion("justificacionSinEvidencia", "Escriba la justificación")  # RF-08-AC-5
    return 1, d.justificacionSinEvidencia.strip()


@router.post("/reports/{folio}/completions")
def complete_report(
    folio: str = FolioP,
    datos: Optional[str] = Form(default=None),
    fotos: list[UploadFile] = File(default=[]),
    idempotency_key: Optional[str] = Header(default=None),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    en_nombre_de = _actor_de_mantenimiento(db, quien, r)
    exigir_transicion(r, "Terminado")  # RF-07-AC-2
    d = _leer_completion(datos)
    if len([f for f in fotos if f.filename]) > MAX_FOTOS_POR_ETAPA:
        raise validacion("fotos", "Máximo 5 fotografías por etapa")
    _validar_textos_de_terminado(d)
    garantia = _garantia(d.garantiaVencimiento)
    aceptados, rechazados = validar_archivos(fotos)
    sin_evidencia, justificacion = _excepcion_sin_evidencia(quien, r, d) if not aceptados else (0, None)
    ciclo = ciclo_actual(db, folio)
    plazo = mas_horas(parametro(db, "plazoConfirmacionHoras"))  # RF-09, RF-27-AC-4
    escritos: list = []
    try:
        with tx(db):
            db.execute("UPDATE reporte SET estado='Terminado' WHERE folio=?", (folio,))
            db.execute(
                """UPDATE ciclo_atencion SET fin=?, nota_trabajo=?, pendientes=?, sin_evidencia_fotografica=?,
                          justificacion_sin_evidencia=?, garantia_vencimiento=?, plazo_confirmacion_hasta=?
                          WHERE reporte_folio=? AND numero=?""",
                (
                    now_utc(),
                    d.notaTrabajo,
                    d.pendientes,
                    sin_evidencia,
                    justificacion,
                    garantia.isoformat() if garantia else None,
                    plazo,
                    folio,
                    ciclo["numero"],
                ),
            )
            comentario = f"Pendiente: {d.pendientes}" if d.pendientes else None  # RF-08-AC-7
            registrar_cambio_estado(db, folio, "EnProceso", "Terminado", quien.id, comentario, en_nombre_de)
            guardar_adjuntos(db, folio, aceptados, rechazados, quien.id, escritos, "Evidencia", ciclo["numero"])
            N.al_cambiar_estado(db, obtener_reporte(db, folio), "Terminado", plazo_hasta=plazo)  # RF-11-AC-9
    except BaseException:
        deshacer_archivos(escritos)
        raise
    despachar(db)
    detalle = detalle_para(db, quien, folio)
    return responder(
        {**detalle, "archivosRechazados": rechazados}, 201, f"/reports/{folio}/completions/{ciclo['numero']}"
    )


# ------------------------------------------------------------------ garantía (RF-25)
@router.put("/reports/{folio}/warranty")
def set_warranty(
    folio: str = FolioP,
    body: Any = Body(...),
    if_match: str = Header(...),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    _actor_de_mantenimiento(db, quien, r)
    verificar_if_match(if_match, detalle_para(db, quien, folio))
    if r["estado"] not in ("Terminado", "Cerrado"):
        raise conflicto("La garantía se registra al terminar el trabajo")
    d = S.parsear(S.WarrantyPut, body)
    try:
        garantia = date.fromisoformat(d.garantiaVencimiento)
    except ValueError:
        raise validacion("garantiaVencimiento", "Fecha no válida (use AAAA-MM-DD)")
    if garantia < hoy():
        raise validacion("garantiaVencimiento", "La fecha de vencimiento no puede ser pasada")  # RF-25-AC-2
    ciclo = ciclo_actual(db, folio)
    with tx(db):
        db.execute(
            "UPDATE ciclo_atencion SET garantia_vencimiento=? WHERE reporte_folio=? AND numero=?",
            (garantia.isoformat(), folio, ciclo["numero"]),
        )
        reclasificacion(db, folio, quien.id, "garantiaVencimiento", ciclo["garantia_vencimiento"], garantia.isoformat())
    return _responder_detalle(db, quien, folio)


# ------------------------------------------------------------------ confirmación del residente (RF-09)
RESPUESTA_LEGIBLE = {"YaQuedo": "Ya quedó", "SigueFallando": "Sigue fallando"}


@router.post("/reports/{folio}/resident-responses")
def respond_as_resident(
    folio: str = FolioP,
    body: Any = Body(...),
    idempotency_key: Optional[str] = Header(default=None),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    if r["reportante_id"] != quien.id:
        raise prohibido("Solo el residente reportante puede responder")
    if r["estado"] != "Terminado":
        raise conflicto("Transición no permitida")
    ciclo = ciclo_actual(db, folio)
    if ciclo["plazo_confirmacion_hasta"] and now_utc() > ciclo["plazo_confirmacion_hasta"]:
        raise conflicto("El plazo para responder terminó")  # RF-09-AC-3
    if db.execute(
        "SELECT 1 FROM confirmacion_residente WHERE reporte_folio=? AND ciclo_numero=?", (folio, ciclo["numero"])
    ).fetchone():
        raise conflicto("Ya respondió en este ciclo")
    d = S.parsear(S.ResidentResponseCreate, body)
    comentario = d.comentario.strip() if d.comentario and d.comentario.strip() else None
    if d.respuesta == "SigueFallando" and not comentario:
        raise validacion("comentario", "Escriba qué sigue fallando")
    if comentario and len(comentario) > 1000:
        raise validacion("comentario", "Máximo 1,000 caracteres")
    with tx(db):
        db.execute(
            """INSERT INTO confirmacion_residente (reporte_folio, ciclo_numero, respuesta, comentario, fecha,
                respondida_por)
                      VALUES (?,?,?,?,?,?)""",
            (folio, ciclo["numero"], d.respuesta, comentario, now_utc(), quien.id),
        )
        N._registrar(
            db,
            folio,
            "RespuestaResidente",
            f"El residente respondió «{RESPUESTA_LEGIBLE[d.respuesta]}» en {folio}."
            + (f" Comentario: «{comentario}»." if comentario else ""),
            f"ReportaYa: respuesta del residente en {folio}",
            N.administracion(db),
        )
    despachar(db)
    c = db.execute(
        "SELECT * FROM confirmacion_residente WHERE reporte_folio=? AND ciclo_numero=?", (folio, ciclo["numero"])
    ).fetchone()
    return responder(
        {"respuesta": c["respuesta"], "comentario": c["comentario"], "fecha": out_dt(c["fecha"])},
        201,
        f"/reports/{folio}/resident-responses/{ciclo['numero']}",
    )


# ------------------------------------------------------------------ cierre (RF-09)
def _condicion_de_cierre(db, r, ciclo) -> tuple[Optional[str], Optional[str]]:
    """(condición que permite cerrar, respuesta del residente). Condición None = todavía no se puede."""
    conf = db.execute(
        "SELECT respuesta FROM confirmacion_residente WHERE reporte_folio=? AND ciclo_numero=?",
        (r["folio"], ciclo["numero"]),
    ).fetchone()
    if conf:
        return ("Respuesta del residente", conf["respuesta"])
    if V.es_area_comun(db, r):
        return ("Área común", None)  # RF-09-AC-6
    if not r["reportante_id"]:
        return ("Reportante sin cuenta", None)  # RF-09-AC-9
    if ciclo["plazo_confirmacion_hasta"] and now_utc() > ciclo["plazo_confirmacion_hasta"]:
        return ("Plazo de confirmación vencido", None)
    return (None, None)


@router.post("/reports/{folio}/closures")
def close_report(
    folio: str = FolioP, body: Any = Body(default={}), db=Depends(get_db), quien: UsuarioSesion = Depends(actor)
):
    r = visible(db, quien, folio)
    exigir_gestion(db, quien)  # RF-09-AC-7, AC-8 (403 vía PERMISOS)
    exigir_transicion(r, "Cerrado")
    ciclo = ciclo_actual(db, folio)
    condicion, respuesta = _condicion_de_cierre(db, r, ciclo)
    if condicion is None:
        raise conflicto(
            f"Esperando confirmación del residente hasta el {fecha_legible(ciclo['plazo_confirmacion_hasta'])}"
        )  # RF-09-AC-2
    d = S.parsear(S.CloseRequest, body)
    motivo = d.motivo.strip() if d.motivo and d.motivo.strip() else None
    if respuesta == "SigueFallando" and not motivo:
        raise validacion("motivo", "Escriba el motivo del cierre")  # RF-09-AC-4
    with tx(db):
        db.execute("UPDATE reporte SET estado='Cerrado' WHERE folio=?", (folio,))
        registrar_cambio_estado(db, folio, "Terminado", "Cerrado", quien.id, motivo or condicion)
        nuevo = obtener_reporte(db, folio)
        N.al_cambiar_estado(db, nuevo, "Cerrado")
        for unido in db.execute("SELECT * FROM reporte WHERE reporte_principal=?", (folio,)).fetchall():
            N.al_cambiar_estado(db, unido, "Cerrado", f"Se cerró el reporte principal {folio}.")  # RF-17-AC-4
    despachar(db)
    return _responder_detalle(db, quien, folio, 201, f"/reports/{folio}/closures/{ciclo['numero']}")


# ------------------------------------------------------------------ cancelación (RF-07)
MOTIVO_RESIDENTE = "Ya se resolvió"


def _normalizar(texto: str) -> str:
    return " ".join(texto.lower().replace("ó", "o").replace(".", "").split())


@router.post("/reports/{folio}/cancellations")
def cancel_report(
    folio: str = FolioP, body: Any = Body(...), db=Depends(get_db), quien: UsuarioSesion = Depends(actor)
):
    r = visible(db, quien, folio)  # RF-07-AC-8: ajeno no visible -> 404
    if quien.rol == RES and r["reportante_id"] != quien.id:
        raise prohibido("Solo el residente que registró el reporte puede cancelarlo")
    exigir_transicion(r, "Cancelado")  # RF-07-AC-3, AC-7
    d = S.parsear(S.CancelRequest, body)
    motivo = (d.motivo or "").strip()
    if quien.rol == RES:
        if _normalizar(motivo) != _normalizar(MOTIVO_RESIDENTE):
            raise validacion("motivo", "Solo puede cancelar un reporte que ya se resolvió")  # RF-07-AC-9
        motivo = MOTIVO_RESIDENTE
    elif not motivo:
        raise validacion("motivo", "El motivo es obligatorio")  # RF-07-AC-5
    if len(motivo) > 500:
        raise validacion("motivo", "Máximo 500 caracteres")
    with tx(db):
        db.execute("UPDATE reporte SET estado='Cancelado' WHERE folio=?", (folio,))
        registrar_cambio_estado(db, folio, r["estado"], "Cancelado", quien.id, motivo)
        nuevo = obtener_reporte(db, folio)
        if quien.rol == RES:
            N.al_cancelar_residente(db, nuevo, motivo)  # RF-11-AC-6
            prop = N._propietario_a_avisar(db, nuevo)
            if prop:
                N._registrar(
                    db,
                    folio,
                    "Estado:Cancelado",
                    f"El reporte {folio} de su unidad fue cancelado: «{motivo}».",
                    f"ReportaYa: {folio} cancelado",
                    correos_sin_cuenta=[prop],
                )
        else:
            N.al_cambiar_estado(db, nuevo, "Cancelado", f"Motivo: «{motivo}».")
    despachar(db)
    return _responder_detalle(db, quien, folio, 201, f"/reports/{folio}/cancellations/1")


# ------------------------------------------------------------------ reapertura (RF-09-AC-5, RF-19)
@router.post("/reports/{folio}/reopenings")
def reopen_report(
    folio: str = FolioP, body: Any = Body(...), db=Depends(get_db), quien: UsuarioSesion = Depends(actor)
):
    r = visible(db, quien, folio)
    exigir_gestion(db, quien)
    exigir_transicion(r, "EnProceso")
    if r["estado"] == "Cerrado" and not dentro_de_plazo_de_reapertura(db, folio):
        raise conflicto("El plazo para reabrir terminó")
    d = S.parsear(S.CommentRequest, body)
    comentario = (d.comentario or "").strip()
    if not comentario:
        raise validacion("comentario", "Escriba el motivo de la reapertura")  # RF-19-AC-5
    if len(comentario) > 1000:
        raise validacion("comentario", "Máximo 1,000 caracteres")
    with tx(db):
        db.execute("UPDATE reporte SET estado='EnProceso' WHERE folio=?", (folio,))
        n = abrir_ciclo(db, folio)  # mismo folio, ciclo nuevo
        registrar_cambio_estado(db, folio, r["estado"], "EnProceso", quien.id, comentario)
        N.al_cambiar_estado(db, obtener_reporte(db, folio), "EnProceso", f"Se reabrió: «{comentario}».")
    despachar(db)
    return _responder_detalle(db, quien, folio, 201, f"/reports/{folio}/reopenings/{n - 1}")


# ------------------------------------------------------------------ duplicados (RF-17)
@router.post("/reports/{folio}/merges")
def merge_report(folio: str = FolioP, body: Any = Body(...), db=Depends(get_db), quien: UsuarioSesion = Depends(actor)):
    r = visible(db, quien, folio)
    exigir_gestion(db, quien)
    exigir_transicion(r, "Unido")
    d = S.parsear(S.MergeRequest, body)
    principal = db.execute("SELECT * FROM reporte WHERE folio=?", (d.reportePrincipal,)).fetchone()
    if not principal or principal["folio"] == folio:
        raise validacion("reportePrincipal", "El reporte principal no existe")
    if principal["estado"] in ("Cancelado", "Unido"):
        raise validacion("reportePrincipal", "El reporte principal está cancelado o unido a otro")
    if (r["fecha_aviso"], r["folio"]) < (principal["fecha_aviso"], principal["folio"]):
        raise validacion("reportePrincipal", "Solo se une el reporte más reciente al más antiguo")
    with tx(db):
        db.execute(
            "UPDATE reporte SET estado='Unido', reporte_principal=?, posible_duplicado_de=NULL WHERE folio=?",
            (principal["folio"], folio),
        )
        registrar_cambio_estado(db, folio, r["estado"], "Unido", quien.id, f"Unido a {principal['folio']}")
        N.al_cambiar_estado(
            db, obtener_reporte(db, folio), "Unido", f"Se unió a {principal['folio']}, que sigue su atención."
        )
        N.al_residente(db, principal, "Union", f"El reporte {folio} se unió a su reporte {principal['folio']}.")
    despachar(db)
    return _responder_detalle(db, quien, folio, 201, f"/reports/{folio}/merges/1")


@router.delete("/reports/{folio}/duplicate-flag")
def keep_independent(folio: str = FolioP, db=Depends(get_db), quien: UsuarioSesion = Depends(actor)):
    r = visible(db, quien, folio)
    exigir_gestion(db, quien)
    if r["posible_duplicado_de"]:
        with tx(db):
            db.execute("UPDATE reporte SET posible_duplicado_de=NULL WHERE folio=?", (folio,))
            reclasificacion(
                db, folio, quien.id, "posibleDuplicado", r["posible_duplicado_de"], "Independiente"
            )  # RF-17-AC-2
    return Response(status_code=204)
