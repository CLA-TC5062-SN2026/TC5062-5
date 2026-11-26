"""Matriz de visibilidad del SRS (sección 2.3), aplicada en el servidor en cada petición (RNF-05).

Una sola definición para listados, detalle, historial, archivos y acciones:
- `condicion_sql(db, quien)`: filtro WHERE de los reportes que ese usuario puede ver.
- `puede_ver(db, quien, r)`: lo mismo para un reporte ya leído. Si no lo ve, el endpoint responde 404
  (SRS 3.0: «no existe o no es visible para ese usuario»), nunca 403, para no revelar que existe.
- `recortar_detalle(...)`: quita del detalle los campos que la matriz niega a ese rol.

Corrige el hallazgo H-1 de S09-A1 (control de acceso por registro ausente).
"""

from typing import Optional

from .security import ADMIN, MANT, RES, VIG, UsuarioSesion
from .util import no_encontrado

ABIERTOS_MANTENIMIENTO = ("Asignado", "EnProceso")
MENSAJE_SIN_ACCESO = "Sin autorización de acceso: coordinar con la Administración"


def vinculacion_vigente(db, residente_id: str):
    """Vinculación activa del Residente (unidad y fecha de inicio), o None."""
    return db.execute(
        """SELECT unidad_id, fecha_inicio FROM vinculacion_unidad
                         WHERE residente_id=? AND fecha_fin IS NULL""",
        (residente_id,),
    ).fetchone()


def condicion_sql(db, quien: UsuarioSesion, alias: str = "r", solo_abiertos_mant: bool = False) -> tuple[str, list]:
    """(expresión SQL, parámetros) con los reportes visibles para `quien`."""
    if quien.rol == ADMIN:
        return "1=1", []
    if quien.rol == VIG:  # RF-04-AC-7: solo los que registró
        return f"{alias}.capturado_por = ?", [quien.id]
    if quien.rol == MANT:  # solo los asignados a él (RF-16)
        cond = f"{alias}.responsable_usuario_id = ?"
        if solo_abiertos_mant:
            cond += f" AND {alias}.estado IN ('Asignado','EnProceso')"
        return cond, [quien.id]
    # Residente (RF-10): los que reportó, los de su unidad desde su vinculación y todos los de áreas comunes
    partes = [
        f"{alias}.reportante_id = ?",
        f"(SELECT tipo FROM ubicacion WHERE id = {alias}.ubicacion_id) = 'AreaComun'",
    ]
    params: list = [quien.id]
    v = vinculacion_vigente(db, quien.id)
    if v:
        partes.append(f"({alias}.ubicacion_id = ? AND {alias}.fecha_aviso >= ?)")
        params += [v["unidad_id"], v["fecha_inicio"]]
    return "(" + " OR ".join(partes) + ")", params


def puede_ver(db, quien: UsuarioSesion, r) -> bool:
    cond, params = condicion_sql(db, quien)
    return (
        db.execute(f"SELECT 1 FROM reporte r WHERE r.folio = ? AND {cond}", [r["folio"], *params]).fetchone()
        is not None
    )


def exigir_visible(db, quien: UsuarioSesion, r) -> None:
    if not puede_ver(db, quien, r):
        raise no_encontrado("Reporte no encontrado")


def es_area_comun(db, r) -> bool:
    return db.execute("SELECT tipo FROM ubicacion WHERE id=?", (r["ubicacion_id"],)).fetchone()["tipo"] == "AreaComun"


def es_su_unidad(db, quien: UsuarioSesion, r) -> bool:
    v = vinculacion_vigente(db, quien.id)
    return bool(v) and v["unidad_id"] == r["ubicacion_id"]


# ----------------------------------------------------------------- recorte de campos
_SOLO_ADMIN = ("montoCosto", "propietario", "capturadoPor", "fechaCaptura")


_NO_VE_VIGILANCIA = (
    "notas",
    "responsable",
    "pagador",
    "responsableCosto",
    "autorizaAcceso",
    "horariosAcceso",
    "fechaVisita",
    "detencionAbierta",
    "ciclos",
)


def _quitar(d: dict, campos) -> None:
    for campo in campos:
        d.pop(campo, None)


def _recortar_para_residente(db, quien: UsuarioSesion, r, d: dict) -> None:
    _quitar(d, ("notas", "responsable"))  # RF-15-AC-3; matriz: «Responsable asignado: No»
    if r["reportante_id"] != quien.id and es_area_comun(db, r):
        d.pop("reportante", None)  # RF-10-AC-3: áreas comunes sin datos del reportante
    if not es_su_unidad(db, quien, r) and r["reportante_id"] != quien.id:
        # Pagador, autorización y horarios: solo de su unidad o de lo que él reportó.
        _quitar(d, ("pagador", "responsableCosto", "autorizaAcceso", "horariosAcceso"))
    for c in d.get("ciclos", []):
        c.pop("justificacionSinEvidencia", None)


def recortar_detalle(db, quien: UsuarioSesion, r, d: dict) -> dict:
    """Detalle del reporte según la matriz 2.3. `d` es el detalle completo (vista de la Administración)."""
    if quien.rol == ADMIN:
        return d
    d = dict(d)
    _quitar(d, _SOLO_ADMIN)  # monto, datos del propietario y quién capturó: solo Administración (RD-07, RF-20, RF-24)
    if quien.rol == RES:
        _recortar_para_residente(db, quien, r, d)
    elif quien.rol == VIG:
        _quitar(d, _NO_VE_VIGILANCIA)
        d["fotosAlta"] = [f for f in d.get("fotosAlta", []) if f.get("_subidoPor") == quien.id]
    elif quien.rol == MANT:
        _quitar(d, ("pagador", "responsableCosto"))  # pagador y monto: no
        if r["autoriza_acceso"] == 0:
            d["mensajeAcceso"] = MENSAJE_SIN_ACCESO  # RF-16-AC-4, RD-06
    return d


def recortar_resumen(quien: UsuarioSesion, r, d: dict) -> dict:
    if quien.rol == MANT and r["autoriza_acceso"] == 0:
        d = {**d, "mensajeAcceso": MENSAJE_SIN_ACCESO}
    return d


def limpiar_internos(d):
    """Quita las claves internas (prefijo «_») antes de responder."""
    if isinstance(d, dict):
        return {k: limpiar_internos(v) for k, v in d.items() if not k.startswith("_")}
    if isinstance(d, list):
        return [limpiar_internos(x) for x in d]
    return d


def archivo_visible(db, quien: UsuarioSesion, r, adjunto) -> bool:
    """Fotos y video (RD-08): el Residente solo las de su unidad o de áreas comunes; Vigilancia solo las que
    subió; Mantenimiento las de sus asignados; Administración todas. Supone que el reporte ya es visible."""
    if quien.rol in (ADMIN, MANT):
        return True
    if quien.rol == VIG:
        return adjunto["subido_por"] == quien.id
    return es_area_comun(db, r) or es_su_unidad(db, quien, r) or r["reportante_id"] == quien.id


def tipo_historial_visible(quien: UsuarioSesion, tipo: str) -> bool:
    """Historial: la Administración todo; Mantenimiento todo menos costos; el Residente solo los cambios de
    estado (y la constancia de avisos que le llegaron); Vigilancia no tiene acceso (403 en PERMISOS)."""
    if quien.rol == ADMIN:
        return True
    if quien.rol == MANT:
        return tipo != "Costo"
    return tipo in ("CambioEstado", "Confirmacion")


def reportante_de(r) -> Optional[str]:
    return r["reportante_id"]
