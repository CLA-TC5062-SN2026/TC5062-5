"""Padrón y catálogo: unidades, áreas comunes, categorías y parámetros (RF-01, RD-01, RF-27)."""
import sqlite3
from typing import Any, Literal, Optional

from fastapi import APIRouter, Body, Depends, Header, Path, Query

from .. import schemas as S
from ..db import get_db, tx
from ..serial import AREA_SQL, UNIT_SQL, area_out, parameter_out, unit_out, b
from ..util import (UUID_RE, ApiError, es_administrador, new_id, no_encontrado, now_utc, out_dt, pagina,
                    paginacion, prohibido, responder, validacion, verificar_if_match, compactar)
from ..security import actor

router = APIRouter()
UnitId = Path(..., pattern=UUID_RE)


# ------------------------------------------------------------------ unidades
def _unit(db, unit_id):
    r = db.execute(UNIT_SQL + " WHERE u.ubicacion_id = ?", (unit_id,)).fetchone()
    if not r:
        raise no_encontrado("Unidad no encontrada")
    return r


@router.get("/units")
def list_units(torre: Optional[str] = None, activa: Optional[bool] = None, db=Depends(get_db),
               pg=Depends(paginacion)):
    where, params = [], []
    if torre is not None:
        where.append("u.torre = ? COLLATE NOCASE"); params.append(torre)
    if activa is not None:
        where.append("b.activa = ?"); params.append(int(activa))
    sql_from = "FROM unidad u JOIN ubicacion b ON b.id = u.ubicacion_id" + (" WHERE " + " AND ".join(where) if where else "")
    sel = """u.ubicacion_id AS id, u.torre, u.piso, u.numero, u.propietario_nombre, u.propietario_correo,
             u.propietario_vive_en_condominio, b.activa"""
    return responder(pagina(db, sql_from, params, sel, "u.torre, u.piso, u.numero", pg, unit_out))


@router.post("/units")
def create_unit(body: Any = Body(...), db=Depends(get_db)):
    d = S.parsear(S.UnitCreate, body)
    torre, numero = S.no_vacio(d.torre, "torre"), S.no_vacio(d.numero, "numero")
    S.no_vacio(d.propietario.nombre, "propietario.nombre")
    if db.execute("SELECT 1 FROM unidad WHERE torre=? AND numero=?", (torre, numero)).fetchone():
        raise validacion("numero", "Ya existe una unidad con esa torre y número")
    uid = new_id()
    with tx(db):
        db.execute("INSERT INTO ubicacion (id, tipo, activa) VALUES (?, 'Unidad', 1)", (uid,))
        db.execute("""INSERT INTO unidad (ubicacion_id, torre, piso, numero, propietario_nombre, propietario_correo,
                      propietario_vive_en_condominio) VALUES (?,?,?,?,?,?,?)""",
                   (uid, torre, d.piso, numero, d.propietario.nombre.strip(), d.propietario.correo,
                    int(d.propietario.viveEnCondominio)))
    return responder(unit_out(_unit(db, uid)), 201, f"/units/{uid}", etag=True)


@router.get("/units/{unitId}")
def get_unit(unitId: str = UnitId, db=Depends(get_db)):
    return responder(unit_out(_unit(db, unitId)), etag=True)


@router.patch("/units/{unitId}")
def update_unit(unitId: str = UnitId, body: Any = Body(...), if_match: str = Header(...), db=Depends(get_db)):
    actual = unit_out(_unit(db, unitId))
    verificar_if_match(if_match, actual)
    d = S.parsear(S.UnitUpdate, body)
    campos = d.model_fields_set
    for c in ("torre", "piso", "numero", "activa"):
        if c in campos and getattr(d, c) is None:
            raise validacion(c, "No admite null")
    torre = S.no_vacio(d.torre, "torre") if "torre" in campos else actual["torre"]
    numero = S.no_vacio(d.numero, "numero") if "numero" in campos else actual["numero"]
    piso = d.piso if "piso" in campos else actual["piso"]
    prop = dict(actual["propietario"])
    if "propietario" in campos:
        if d.propietario is None:
            raise validacion("propietario", "No admite null")
        for k in d.propietario.model_fields_set:
            v = getattr(d.propietario, k)
            if v is None:
                raise validacion(f"propietario.{k}", "No admite null")
            prop[k] = v
    S.no_vacio(prop["nombre"], "propietario.nombre")
    if db.execute("SELECT 1 FROM unidad WHERE torre=? AND numero=? AND ubicacion_id<>?", (torre, numero, unitId)).fetchone():
        raise validacion("numero", "Ya existe una unidad con esa torre y número")
    with tx(db):
        db.execute("""UPDATE unidad SET torre=?, piso=?, numero=?, propietario_nombre=?, propietario_correo=?,
                      propietario_vive_en_condominio=? WHERE ubicacion_id=?""",
                   (torre, piso, numero, prop["nombre"].strip(), prop["correo"], int(prop["viveEnCondominio"]), unitId))
        if "activa" in campos:
            db.execute("UPDATE ubicacion SET activa=? WHERE id=?", (int(d.activa), unitId))
    return responder(unit_out(_unit(db, unitId)), etag=True)


# ------------------------------------------------------------------ áreas comunes
def _area(db, area_id):
    r = db.execute(AREA_SQL + " WHERE a.ubicacion_id = ?", (area_id,)).fetchone()
    if not r:
        raise no_encontrado("Área común no encontrada")
    return r


@router.get("/common-areas")
def list_common_areas(activa: Optional[bool] = None, db=Depends(get_db)):
    sql, params = AREA_SQL, []
    if activa is not None:
        sql += " WHERE b.activa = ?"; params.append(int(activa))
    return responder([area_out(r) for r in db.execute(sql + " ORDER BY a.nombre", params).fetchall()])


@router.post("/common-areas")
def create_common_area(body: Any = Body(...), db=Depends(get_db)):
    d = S.parsear(S.CommonAreaCreate, body)
    nombre = S.no_vacio(d.nombre, "nombre")
    if db.execute("SELECT 1 FROM area_comun WHERE nombre=?", (nombre,)).fetchone():
        raise validacion("nombre", "Ya existe un área común con ese nombre")
    aid = new_id()
    with tx(db):
        db.execute("INSERT INTO ubicacion (id, tipo, activa) VALUES (?, 'AreaComun', 1)", (aid,))
        db.execute("INSERT INTO area_comun (ubicacion_id, nombre) VALUES (?, ?)", (aid, nombre))
    return responder(area_out(_area(db, aid)), 201, f"/common-areas/{aid}", etag=True)


@router.get("/common-areas/{areaId}")
def get_common_area(areaId: str = Path(..., pattern=UUID_RE), db=Depends(get_db)):
    return responder(area_out(_area(db, areaId)), etag=True)


@router.patch("/common-areas/{areaId}")
def update_common_area(areaId: str = Path(..., pattern=UUID_RE), body: Any = Body(...),
                       if_match: str = Header(...), db=Depends(get_db)):
    actual = area_out(_area(db, areaId))
    verificar_if_match(if_match, actual)
    d = S.parsear(S.CommonAreaUpdate, body)
    campos = d.model_fields_set
    for c in ("nombre", "activa"):
        if c in campos and getattr(d, c) is None:
            raise validacion(c, "No admite null")
    nombre = S.no_vacio(d.nombre, "nombre") if "nombre" in campos else actual["nombre"]
    if db.execute("SELECT 1 FROM area_comun WHERE nombre=? AND ubicacion_id<>?", (nombre, areaId)).fetchone():
        raise validacion("nombre", "Ya existe un área común con ese nombre")
    with tx(db):
        db.execute("UPDATE area_comun SET nombre=? WHERE ubicacion_id=?", (nombre, areaId))
        if "activa" in campos:
            db.execute("UPDATE ubicacion SET activa=? WHERE id=?", (int(d.activa), areaId))
    return responder(area_out(_area(db, areaId)), etag=True)


# ------------------------------------------------------------------ categorías (solo lectura: RD-01)
@router.get("/categories")
def list_categories(db=Depends(get_db)):
    out = []
    for c in db.execute("SELECT * FROM categoria ORDER BY rowid").fetchall():
        subs = db.execute("SELECT nombre, prioridad_sugerida FROM subtipo WHERE categoria_id=? ORDER BY rowid", (c["id"],)).fetchall()
        out.append({"id": c["id"], "nombre": c["nombre"], "prioridadSugerida": c["prioridad_sugerida"],
                    "subtipos": [{"nombre": s["nombre"], "prioridadSugerida": s["prioridad_sugerida"]} for s in subs]})
    return responder(out)


# ------------------------------------------------------------------ parámetros (RF-27)
@router.get("/parameters")
def list_parameters(db=Depends(get_db)):
    return responder([parameter_out(r) for r in db.execute("SELECT * FROM parametro ORDER BY rowid").fetchall()])


@router.put("/parameters/{clave}")
def update_parameter(clave: str, body: Any = Body(...), db=Depends(get_db), quien=Depends(actor)):
    p = db.execute("SELECT * FROM parametro WHERE clave=?", (clave,)).fetchone()
    if not p:
        raise no_encontrado("Parámetro no encontrado")
    if not es_administrador(db, quien["id"]):
        raise prohibido("Solo el Administrador modifica parámetros")
    d = S.parsear(S.ParameterUpdate, body)
    if d.valor <= 0:
        raise validacion("valor", "El valor debe ser mayor que cero")
    with tx(db):
        db.execute("UPDATE parametro SET valor=? WHERE clave=?", (d.valor, clave))
        db.execute("""INSERT INTO cambio_parametro (clave, valor_anterior, valor_nuevo, fecha, modificado_por)
                      VALUES (?,?,?,?,?)""", (clave, p["valor"], d.valor, now_utc(), quien["id"]))
    return responder(parameter_out(db.execute("SELECT * FROM parametro WHERE clave=?", (clave,)).fetchone()))


@router.get("/parameters/{clave}/changes")
def list_parameter_changes(clave: str, db=Depends(get_db)):
    if not db.execute("SELECT 1 FROM parametro WHERE clave=?", (clave,)).fetchone():
        raise no_encontrado("Parámetro no encontrado")
    filas = db.execute("""SELECT c.*, u.nombre AS usuario FROM cambio_parametro c JOIN usuario u ON u.id = c.modificado_por
                          WHERE c.clave=? ORDER BY c.id DESC""", (clave,)).fetchall()
    return responder([{"clave": f["clave"], "valorAnterior": f["valor_anterior"], "valorNuevo": f["valor_nuevo"],
                       "usuario": f["usuario"], "fecha": out_dt(f["fecha"])} for f in filas])
