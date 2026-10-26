"""Usuarios, vinculaciones, responsables, proveedores sin acceso y delegaciones (RF-01, RF-02, RF-21)."""
import sqlite3
from typing import Any, Literal, Optional

from fastapi import APIRouter, Body, Depends, Header, Path, Query

from .. import schemas as S
from ..db import get_db, tx
from ..serial import UNIT_SQL, b, delegation_out, provider_out, user_out, vinculacion_out
from ..util import (UUID_RE, es_administrador, new_id, no_encontrado, now_utc, pagina, paginacion, prohibido,
                    responder, to_utc, validacion, verificar_if_match, conflicto)
from ..security import actor

router = APIRouter()
UserId = Path(..., pattern=UUID_RE)


def _user(db, user_id):
    r = db.execute("SELECT * FROM usuario WHERE id=?", (user_id,)).fetchone()
    if not r:
        raise no_encontrado("Usuario no encontrado")
    return r


def _unidad_valida(db, unidad_id, campo):
    u = db.execute("SELECT b.activa FROM unidad u JOIN ubicacion b ON b.id=u.ubicacion_id WHERE u.ubicacion_id=?",
                   (unidad_id,)).fetchone()
    if not u:
        raise validacion(campo, "La unidad no existe")
    if not u["activa"]:
        raise validacion(campo, "La unidad está desactivada")


# ------------------------------------------------------------------ usuarios
@router.get("/users")
def list_users(rol: Optional[S.Rol] = None,
               estadoCuenta: Optional[Literal["PendienteActivacion", "Activa", "Desactivada"]] = None,
               unidadId: Optional[str] = Query(None, pattern=UUID_RE), db=Depends(get_db), pg=Depends(paginacion)):
    where, params = [], []
    if rol:
        where.append("u.rol=?"); params.append(rol)
    if estadoCuenta:
        where.append("u.estado_cuenta=?"); params.append(estadoCuenta)
    if unidadId:
        where.append("EXISTS (SELECT 1 FROM vinculacion_unidad v WHERE v.residente_id=u.id AND v.unidad_id=? AND v.fecha_fin IS NULL)")
        params.append(unidadId)
    sql_from = "FROM usuario u" + (" WHERE " + " AND ".join(where) if where else "")
    return responder(pagina(db, sql_from, params, "u.*", "u.nombre COLLATE NOCASE, u.rowid", pg, lambda r: user_out(db, r)))


@router.post("/users")
def create_user(body: Any = Body(...), db=Depends(get_db)):
    d = S.parsear(S.UserCreate, body)
    nombre = S.no_vacio(d.nombre, "nombre")
    if d.rol != "Residente" and d.vinculacion:
        raise validacion("vinculacion", "Solo aplica al rol Residente")
    if d.rol != "Mantenimiento" and d.mantenimiento:
        raise validacion("mantenimiento", "Solo aplica al rol Mantenimiento")
    if d.rol != "Administracion" and d.perfilAdministracion:
        raise validacion("perfilAdministracion", "Solo aplica al rol Administracion")
    fecha_inicio = None
    if d.rol == "Residente":
        if not d.vinculacion:
            raise validacion("vinculacion", "Campo obligatorio para un Residente")
        _unidad_valida(db, d.vinculacion.unidadId, "vinculacion.unidadId")
        fecha_inicio = to_utc(d.vinculacion.fechaInicio, "vinculacion.fechaInicio")
    if d.rol == "Mantenimiento":
        if not d.mantenimiento:
            raise validacion("mantenimiento", "Campo obligatorio para el rol Mantenimiento")
        if d.mantenimiento.tipo == "ProveedorExterno":
            S.no_vacio(d.mantenimiento.especialidad, "mantenimiento.especialidad")
            S.no_vacio(d.mantenimiento.telefono, "mantenimiento.telefono")
    if d.rol == "Administracion" and not d.perfilAdministracion:
        raise validacion("perfilAdministracion", "Campo obligatorio para el rol Administracion")
    if db.execute("SELECT 1 FROM usuario WHERE correo=?", (d.correo,)).fetchone():
        raise validacion("correo", "Ya existe un usuario con ese correo")
    uid = new_id()
    with tx(db):
        db.execute("INSERT INTO usuario (id, nombre, correo, rol, estado_cuenta) VALUES (?,?,?,?, 'PendienteActivacion')",
                   (uid, nombre, d.correo, d.rol))
        if d.rol == "Residente":
            db.execute("INSERT INTO residente (usuario_id) VALUES (?)", (uid,))
            db.execute("""INSERT INTO vinculacion_unidad (id, residente_id, unidad_id, ocupacion, fecha_inicio)
                          VALUES (?,?,?,?,?)""", (new_id(), uid, d.vinculacion.unidadId, d.vinculacion.ocupacion, fecha_inicio))
        elif d.rol == "Vigilancia":
            db.execute("INSERT INTO vigilante (usuario_id) VALUES (?)", (uid,))
        elif d.rol == "Mantenimiento":
            m = d.mantenimiento
            db.execute("INSERT INTO usuario_mantenimiento (usuario_id, tipo, especialidad, telefono) VALUES (?,?,?,?)",
                       (uid, m.tipo, m.especialidad, m.telefono))
        else:
            db.execute("INSERT INTO usuario_administracion (usuario_id, perfil_administracion) VALUES (?,?)",
                       (uid, d.perfilAdministracion))
    return responder(user_out(db, _user(db, uid)), 201, f"/users/{uid}", etag=True)


@router.get("/users/{userId}")
def get_user(userId: str = UserId, db=Depends(get_db)):
    return responder(user_out(db, _user(db, userId)), etag=True)


@router.patch("/users/{userId}")
def update_user(userId: str = UserId, body: Any = Body(...), if_match: str = Header(...), db=Depends(get_db)):
    u = _user(db, userId)
    verificar_if_match(if_match, user_out(db, u))
    d = S.parsear(S.UserUpdate, body)
    campos = d.model_fields_set
    for c in ("nombre", "correo", "estadoCuenta", "mantenimiento"):
        if c in campos and getattr(d, c) is None:
            raise validacion(c, "No admite null")
    nombre = S.no_vacio(d.nombre, "nombre") if "nombre" in campos else u["nombre"]
    correo = d.correo if "correo" in campos else u["correo"]
    if db.execute("SELECT 1 FROM usuario WHERE correo=? AND id<>?", (correo, userId)).fetchone():
        raise validacion("correo", "Ya existe un usuario con ese correo")
    estado = u["estado_cuenta"]
    if "estadoCuenta" in campos:
        if d.estadoCuenta == "Activa":
            # Solo reactiva una cuenta Desactivada que ya fue activada (tiene contraseña); la pendiente se activa con su enlace.
            if u["estado_cuenta"] != "Desactivada" or u["contrasena_hash"] is None:
                raise conflicto("Solo se reactiva una cuenta desactivada que ya había sido activada")
        estado = d.estadoCuenta
    mant = None
    if "mantenimiento" in campos:
        if u["rol"] != "Mantenimiento":
            raise validacion("mantenimiento", "Solo aplica al rol Mantenimiento")
        actual = db.execute("SELECT * FROM usuario_mantenimiento WHERE usuario_id=?", (userId,)).fetchone()
        mant = {"tipo": actual["tipo"], "especialidad": actual["especialidad"], "telefono": actual["telefono"]}
        for k in d.mantenimiento.model_fields_set:
            v = getattr(d.mantenimiento, k)
            if k == "tipo" and v is None:
                raise validacion("mantenimiento.tipo", "No admite null")
            mant[k] = v
        if mant["tipo"] == "ProveedorExterno":
            S.no_vacio(mant["especialidad"], "mantenimiento.especialidad")
            S.no_vacio(mant["telefono"], "mantenimiento.telefono")
    with tx(db):
        db.execute("UPDATE usuario SET nombre=?, correo=?, estado_cuenta=? WHERE id=?", (nombre, correo, estado, userId))
        if mant:
            db.execute("UPDATE usuario_mantenimiento SET tipo=?, especialidad=?, telefono=? WHERE usuario_id=?",
                       (mant["tipo"], mant["especialidad"], mant["telefono"], userId))
    return responder(user_out(db, _user(db, userId)), etag=True)


# ------------------------------------------------------------------ vinculaciones residente <-> unidad
@router.get("/users/{userId}/unit-links")
def list_unit_links(userId: str = UserId, db=Depends(get_db)):
    _user(db, userId)
    filas = db.execute("SELECT * FROM vinculacion_unidad WHERE residente_id=? ORDER BY fecha_inicio DESC, rowid DESC", (userId,)).fetchall()
    return responder([vinculacion_out(db, f) for f in filas])


@router.post("/users/{userId}/unit-links")
def create_unit_link(userId: str = UserId, body: Any = Body(...), db=Depends(get_db)):
    u = _user(db, userId)
    d = S.parsear(S.VinculacionCreate, body)
    if u["rol"] != "Residente":
        raise validacion("userId", "Solo un Residente tiene vinculaciones")
    _unidad_valida(db, d.unidadId, "unidadId")
    inicio = to_utc(d.fechaInicio, "fechaInicio")
    activa = db.execute("SELECT * FROM vinculacion_unidad WHERE residente_id=? AND fecha_fin IS NULL", (userId,)).fetchone()
    if activa and inicio < activa["fecha_inicio"]:
        raise validacion("fechaInicio", "No puede ser anterior al inicio de la vinculación vigente")
    vid = new_id()
    with tx(db):
        if activa:  # a lo sumo una vinculación activa por residente
            db.execute("UPDATE vinculacion_unidad SET fecha_fin=? WHERE id=?", (inicio, activa["id"]))
        db.execute("INSERT INTO vinculacion_unidad (id, residente_id, unidad_id, ocupacion, fecha_inicio) VALUES (?,?,?,?,?)",
                   (vid, userId, d.unidadId, d.ocupacion, inicio))
    nueva = db.execute("SELECT * FROM vinculacion_unidad WHERE id=?", (vid,)).fetchone()
    return responder(vinculacion_out(db, nueva), 201, f"/users/{userId}/unit-links/{vid}")


# ------------------------------------------------------------------ responsables asignables
@router.get("/assignees")
def list_assignees(db=Depends(get_db)):
    out = []
    for r in db.execute("""SELECT u.id, u.nombre, m.tipo, m.especialidad FROM usuario u
                           JOIN usuario_mantenimiento m ON m.usuario_id=u.id
                           WHERE u.estado_cuenta <> 'Desactivada' ORDER BY u.nombre COLLATE NOCASE""").fetchall():
        out.append({"id": r["id"], "tipo": r["tipo"], "nombre": r["nombre"], "especialidad": r["especialidad"], "sinAcceso": False})
    for r in db.execute("SELECT * FROM proveedor_sin_acceso WHERE activo=1 ORDER BY nombre COLLATE NOCASE").fetchall():
        out.append({"id": r["id"], "tipo": "ProveedorExterno", "nombre": r["nombre"], "especialidad": r["especialidad"], "sinAcceso": True})
    return responder(out)


# ------------------------------------------------------------------ proveedores sin acceso
def _provider(db, pid):
    r = db.execute("SELECT * FROM proveedor_sin_acceso WHERE id=?", (pid,)).fetchone()
    if not r:
        raise no_encontrado("Proveedor no encontrado")
    return r


@router.get("/external-providers")
def list_external_providers(activo: Optional[bool] = None, db=Depends(get_db), pg=Depends(paginacion)):
    where, params = "", []
    if activo is not None:
        where, params = " WHERE activo=?", [int(activo)]
    return responder(pagina(db, "FROM proveedor_sin_acceso" + where, params, "*", "nombre COLLATE NOCASE, rowid", pg, provider_out))


@router.post("/external-providers")
def create_external_provider(body: Any = Body(...), db=Depends(get_db)):
    d = S.parsear(S.ExternalProviderCreate, body)
    nombre, esp, tel = S.no_vacio(d.nombre, "nombre"), S.no_vacio(d.especialidad, "especialidad"), S.no_vacio(d.telefono, "telefono")
    pid = new_id()
    with tx(db):
        db.execute("INSERT INTO proveedor_sin_acceso (id, nombre, especialidad, telefono) VALUES (?,?,?,?)", (pid, nombre, esp, tel))
    return responder(provider_out(_provider(db, pid)), 201, f"/external-providers/{pid}", etag=True)


@router.get("/external-providers/{providerId}")
def get_external_provider(providerId: str = Path(..., pattern=UUID_RE), db=Depends(get_db)):
    return responder(provider_out(_provider(db, providerId)), etag=True)


@router.patch("/external-providers/{providerId}")
def update_external_provider(providerId: str = Path(..., pattern=UUID_RE), body: Any = Body(...),
                             if_match: str = Header(...), db=Depends(get_db)):
    actual = provider_out(_provider(db, providerId))
    verificar_if_match(if_match, actual)
    d = S.parsear(S.ExternalProviderUpdate, body)
    campos = d.model_fields_set
    nuevo = dict(actual)
    for c in ("nombre", "especialidad", "telefono", "activo"):
        if c in campos:
            v = getattr(d, c)
            if v is None:
                raise validacion(c, "No admite null")
            nuevo[c] = S.no_vacio(v, c) if c != "activo" else v
    with tx(db):
        db.execute("UPDATE proveedor_sin_acceso SET nombre=?, especialidad=?, telefono=?, activo=? WHERE id=?",
                   (nuevo["nombre"], nuevo["especialidad"], nuevo["telefono"], int(nuevo["activo"]), providerId))
    return responder(provider_out(_provider(db, providerId)), etag=True)


# ------------------------------------------------------------------ delegaciones (RF-21)
def _deleg(db, did):
    r = db.execute("SELECT * FROM delegacion WHERE id=?", (did,)).fetchone()
    if not r:
        raise no_encontrado("Delegación no encontrada")
    return r


@router.get("/delegations")
def list_delegations(vigente: Optional[bool] = None, db=Depends(get_db)):
    sql, params = "SELECT * FROM delegacion", []
    if vigente is not None:
        cond = "(habilitada=1 AND (fecha_fin IS NULL OR fecha_fin > ?))"
        sql += " WHERE " + (cond if vigente else "NOT " + cond)
        params.append(now_utc())
    return responder([delegation_out(r) for r in db.execute(sql + " ORDER BY fecha_inicio DESC, rowid DESC", params).fetchall()])


@router.post("/delegations")
def create_delegation(body: Any = Body(...), db=Depends(get_db), quien=Depends(actor)):
    if not es_administrador(db, quien["id"]):
        raise prohibido("Solo el Administrador delega")
    d = S.parsear(S.DelegationCreate, body)
    aux = db.execute("SELECT 1 FROM usuario_administracion WHERE usuario_id=? AND perfil_administracion='Auxiliar'",
                     (d.auxiliarId,)).fetchone()
    if not aux:
        raise validacion("auxiliarId", "No corresponde a un usuario con perfil Auxiliar")
    ahora = now_utc()
    fin = to_utc(d.fechaFin, "fechaFin") if d.fechaFin else None
    if fin and fin <= ahora:
        raise validacion("fechaFin", "Debe ser posterior al momento actual")
    if db.execute("SELECT 1 FROM delegacion WHERE auxiliar_id=? AND habilitada=1 AND fecha_fin IS NULL", (d.auxiliarId,)).fetchone():
        raise conflicto("La Auxiliar ya tiene una delegación vigente sin fecha de fin")
    did = new_id()
    with tx(db):
        db.execute("""INSERT INTO delegacion (id, otorgada_por, auxiliar_id, habilitada, fecha_inicio, fecha_fin)
                      VALUES (?,?,?,1,?,?)""", (did, quien["id"], d.auxiliarId, ahora, fin))
    return responder(delegation_out(_deleg(db, did)), 201, f"/delegations/{did}")


@router.patch("/delegations/{delegationId}")
def update_delegation(delegationId: str = Path(..., pattern=UUID_RE), body: Any = Body(...), db=Depends(get_db),
                      quien=Depends(actor)):
    r = _deleg(db, delegationId)
    if not es_administrador(db, quien["id"]):
        raise prohibido("Solo el Administrador modifica delegaciones")
    d = S.parsear(S.DelegationUpdate, body)
    campos = d.model_fields_set
    habil = r["habilitada"]
    fin = r["fecha_fin"]
    if "habilitada" in campos:
        if d.habilitada is None:
            raise validacion("habilitada", "No admite null")
        habil = int(d.habilitada)
    if "fechaFin" in campos:  # merge-patch: null borra la fecha de fin
        fin = to_utc(d.fechaFin, "fechaFin") if d.fechaFin else None
        if fin and fin < r["fecha_inicio"]:
            raise validacion("fechaFin", "No puede ser anterior al inicio")
    if habil and fin is None and db.execute(
            "SELECT 1 FROM delegacion WHERE auxiliar_id=? AND habilitada=1 AND fecha_fin IS NULL AND id<>?",
            (r["auxiliar_id"], delegationId)).fetchone():
        raise validacion("habilitada", "La Auxiliar ya tiene otra delegación vigente sin fecha de fin")
    with tx(db):
        db.execute("UPDATE delegacion SET habilitada=?, fecha_fin=? WHERE id=?", (habil, fin, delegationId))
    return responder(delegation_out(_deleg(db, delegationId)))
