"""Módulo de autenticación (S05-S06-A2): registro, inicio de sesión con JWT y usuario actual."""
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends

from .. import config, schemas as S
from ..db import get_db, tx
from ..security import (BCRYPT_MAX_BYTES, HASH_RELLENO, crear_token, hash_password, usuario_actual,
                        verify_password)
from ..serial import UNIT_SQL, unit_out, user_out
from ..util import ApiError, new_id, now_utc, responder, validacion
from .usuarios import _unidad_valida

router = APIRouter(prefix="/auth", tags=["Autenticación"])

MAX_INTENTOS = 5          # RNF-06: 5 intentos fallidos ...
BLOQUEO_MINUTOS = 15      # ... bloquean la cuenta 15 minutos


def _credenciales_invalidas() -> ApiError:
    # Mismo mensaje si el correo no existe, la contraseña es incorrecta, la cuenta no está activa o está
    # bloqueada: no se revela cuál falló (RF-01-AC-2, RNF-06).
    return ApiError(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos")


def sesion_usuario(db, u) -> dict:
    """Esquema SesionUsuario del YAML."""
    d = {"id": u["id"], "nombre": u["nombre"], "rol": u["rol"]}
    if u["rol"] == "Administracion":
        a = db.execute("SELECT perfil_administracion FROM usuario_administracion WHERE usuario_id=?", (u["id"],)).fetchone()
        if a:
            d["perfilAdministracion"] = a["perfil_administracion"]
            if a["perfil_administracion"] == "Auxiliar":
                d["delegacionVigente"] = db.execute(
                    """SELECT 1 FROM delegacion WHERE auxiliar_id=? AND habilitada=1
                       AND (fecha_fin IS NULL OR fecha_fin > ?)""", (u["id"], now_utc())).fetchone() is not None
    elif u["rol"] == "Residente":
        v = db.execute("SELECT unidad_id FROM vinculacion_unidad WHERE residente_id=? AND fecha_fin IS NULL", (u["id"],)).fetchone()
        if v:
            d["unidad"] = unit_out(db.execute(UNIT_SQL + " WHERE u.ubicacion_id=?", (v["unidad_id"],)).fetchone())
    return d


def _validar_password(password: str) -> None:
    if len(password) < 8:
        raise validacion("password", "Mínimo 8 caracteres")
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise validacion("password", f"Máximo {BCRYPT_MAX_BYTES} bytes")


@router.post("/register", status_code=201)
def register(body: Any = Body(...), db=Depends(get_db)):
    """Registro público de un Residente de una unidad existente. El rol es siempre Residente."""
    d = S.parsear(S.Registro, body)
    nombre = S.no_vacio(d.nombre, "nombre")
    _validar_password(d.password)
    _unidad_valida(db, d.unidadId, "unidadId")
    if db.execute("SELECT 1 FROM usuario WHERE correo=?", (d.correo,)).fetchone():
        raise validacion("correo", "Ya existe un usuario con ese correo")
    uid, ahora = new_id(), now_utc()
    with tx(db):
        db.execute("""INSERT INTO usuario (id, nombre, correo, rol, estado_cuenta, contrasena_hash)
                      VALUES (?,?,?, 'Residente', 'Activa', ?)""", (uid, nombre, d.correo, hash_password(d.password)))
        db.execute("INSERT INTO residente (usuario_id) VALUES (?)", (uid,))
        db.execute("""INSERT INTO vinculacion_unidad (id, residente_id, unidad_id, ocupacion, fecha_inicio)
                      VALUES (?,?,?,?,?)""", (new_id(), uid, d.unidadId, d.ocupacion, ahora))
    u = db.execute("SELECT * FROM usuario WHERE id=?", (uid,)).fetchone()
    return responder(user_out(db, u), 201, f"/users/{uid}")   # user_out no incluye contrasena_hash


@router.post("/login")
def login(body: Any = Body(...), db=Depends(get_db)):
    d = S.parsear(S.Credenciales, body)
    u = db.execute("SELECT * FROM usuario WHERE correo=?", (d.correo,)).fetchone()
    if not u:
        verify_password(d.password, HASH_RELLENO)  # mismo tiempo de respuesta que con un correo existente
        raise _credenciales_invalidas()
    ahora = datetime.now(timezone.utc)
    if u["bloqueado_hasta"] and datetime.strptime(u["bloqueado_hasta"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > ahora:
        raise _credenciales_invalidas()
    if not verify_password(d.password, u["contrasena_hash"]):
        intentos = u["intentos_fallidos"] + 1
        if intentos >= MAX_INTENTOS:
            hasta = (ahora + timedelta(minutes=BLOQUEO_MINUTOS)).strftime("%Y-%m-%dT%H:%M:%SZ")
            db.execute("UPDATE usuario SET intentos_fallidos=0, bloqueado_hasta=? WHERE id=?", (hasta, u["id"]))
        else:
            db.execute("UPDATE usuario SET intentos_fallidos=? WHERE id=?", (intentos, u["id"]))
        raise _credenciales_invalidas()
    if u["estado_cuenta"] != "Activa":
        raise _credenciales_invalidas()
    db.execute("UPDATE usuario SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?", (u["id"],))
    return responder({"token": crear_token(u), "tipo": "Bearer", "expiraEn": config.JWT_EXPIRATION * 60,
                      "usuario": sesion_usuario(db, u)})


@router.get("/me")
def me(usuario=Depends(usuario_actual), db=Depends(get_db)):
    return responder(sesion_usuario(db, usuario))
