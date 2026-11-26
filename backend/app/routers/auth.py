"""Autenticación (RF-01, RF-14, RNF-06): inicio de sesión con JWT, usuario actual, activación de cuentas y
recuperación de contraseña. No hay registro público: toda cuenta la crea la Administración (RF-02, EX-08)."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, Response

from .. import config, schemas as S
from ..db import get_db, tx
from ..security import (
    BCRYPT_MAX_BYTES,
    HASH_RELLENO,
    UsuarioSesion,
    crear_token,
    hash_password,
    usuario_actual,
    verify_password,
)
from ..serial import UNIT_SQL, unit_out
from ..util import ApiError, now_utc, responder, validacion
from .. import cuentas

router = APIRouter(prefix="/auth", tags=["Autenticación"])
cuentas_router = APIRouter(tags=["Cuentas"])  # rutas públicas fuera de /auth (contrato: /account-activations, ...)

MAX_INTENTOS = 5  # RNF-06: 5 intentos fallidos ...
BLOQUEO_MINUTOS = 15  # ... bloquean la cuenta 15 minutos


def _credenciales_invalidas() -> ApiError:
    # Mismo mensaje si el correo no existe, la contraseña es incorrecta, la cuenta no está activa o está
    # bloqueada: no se revela cuál falló (RF-01-AC-2, RNF-06).
    return ApiError(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos")


def sesion_usuario(db, u: UsuarioSesion) -> dict:
    """Esquema SesionUsuario del YAML."""
    d: dict[str, Any] = {"id": u.id, "nombre": u.nombre, "rol": u.rol}
    if u.rol == "Administracion":
        a = db.execute(
            "SELECT perfil_administracion FROM usuario_administracion WHERE usuario_id=?", (u.id,)
        ).fetchone()
        if a:
            d["perfilAdministracion"] = a["perfil_administracion"]
            if a["perfil_administracion"] == "Auxiliar":
                d["delegacionVigente"] = (
                    db.execute(
                        """SELECT 1 FROM delegacion WHERE auxiliar_id=? AND habilitada=1
                       AND (fecha_fin IS NULL OR fecha_fin > ?)""",
                        (u.id, now_utc()),
                    ).fetchone()
                    is not None
                )
    elif u.rol == "Residente":
        v = db.execute(
            "SELECT unidad_id FROM vinculacion_unidad WHERE residente_id=? AND fecha_fin IS NULL", (u.id,)
        ).fetchone()
        if v:
            d["unidad"] = unit_out(db.execute(UNIT_SQL + " WHERE u.ubicacion_id=?", (v["unidad_id"],)).fetchone())
    return d


def _validar_password(password: str) -> None:
    if len(password) < 8:
        raise validacion("password", "La contraseña debe tener al menos 8 caracteres")
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise validacion("password", f"Máximo {BCRYPT_MAX_BYTES} bytes")


@router.post("/login")
def login(body: Any = Body(...), db=Depends(get_db)):
    d = S.parsear(S.Credenciales, body)
    u = db.execute("SELECT * FROM usuario WHERE correo=?", (d.correo,)).fetchone()
    if not u:
        verify_password(d.password, HASH_RELLENO)  # mismo tiempo de respuesta que con un correo existente
        raise _credenciales_invalidas()
    ahora = datetime.now(timezone.utc)
    if (
        u["bloqueado_hasta"]
        and datetime.strptime(u["bloqueado_hasta"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > ahora
    ):
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
    return responder(
        {
            "token": crear_token(u),
            "tipo": "Bearer",
            "expiraEn": config.JWT_EXPIRATION * 60,
            "usuario": sesion_usuario(db, UsuarioSesion.de_fila(u)),
        }
    )


@router.get("/me")
def me(usuario: UsuarioSesion = Depends(usuario_actual), db=Depends(get_db)):
    return responder(sesion_usuario(db, usuario))


# ------------------------------------------------------------------ activación y recuperación (RF-14)
def _definir_password(db, body, tipo: str) -> Response:
    d = S.parsear(S.TokenPassword, body)
    e, motivo = cuentas.enlace_vigente(db, d.token, tipo)
    if motivo:
        raise validacion("token", motivo)  # RF-14-AC-2
    _validar_password(d.password)
    with tx(db):
        db.execute(
            "UPDATE enlace_acceso SET usado_en=? WHERE hash_token=?", (now_utc(), e["hash_token"])
        )  # un solo uso
        if tipo == "Activacion":
            db.execute(
                """UPDATE usuario SET contrasena_hash=?, estado_cuenta='Activa', intentos_fallidos=0,
                          bloqueado_hasta=NULL WHERE id=? AND estado_cuenta='PendienteActivacion'""",
                (hash_password(d.password), e["usuario_id"]),
            )
        else:
            db.execute(
                "UPDATE usuario SET contrasena_hash=?, intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?",
                (hash_password(d.password), e["usuario_id"]),
            )
    return Response(status_code=204)


@cuentas_router.post("/account-activations")
def activate_account(body: Any = Body(...), db=Depends(get_db)):
    """RF-14-AC-1: con el enlace vigente define su contraseña; la cuenta pasa a «Activa» y el enlace deja de servir."""
    return _definir_password(db, body, "Activacion")


@cuentas_router.post("/password-reset-requests", status_code=202)
def request_password_reset(body: Any = Body(...), db=Depends(get_db)):
    """RF-14-AC-3: misma respuesta exista o no el correo, para no revelar qué correos están registrados."""
    d = S.parsear(S.ResetRequest, body)
    u = db.execute(
        "SELECT id, nombre, correo FROM usuario WHERE correo=? AND estado_cuenta='Activa'", (d.correo,)
    ).fetchone()
    if u:
        with tx(db):
            token = cuentas.emitir(db, u["id"], "Recuperacion")
        cuentas.enviar_recuperacion(u["nombre"], u["correo"], token)
    return responder(
        {"mensaje": "Si el correo está registrado, le enviamos un enlace para definir una contraseña nueva."}, 202
    )


@cuentas_router.post("/password-resets")
def reset_password(body: Any = Body(...), db=Depends(get_db)):
    return _definir_password(db, body, "Recuperacion")
