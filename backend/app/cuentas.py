"""Enlaces de activación y de recuperación de contraseña (RF-14).

Solo se guarda el hash SHA-256 del token (`enlace_acceso.hash_token`); el token en claro viaja una sola vez,
en el correo. Activación: un solo uso, vence en 72 h. Recuperación: un solo uso, vence en 1 h.
"""

import hashlib
import secrets
from datetime import timedelta

from . import config, reloj
from .notificaciones import correo_directo
from .util import now_utc

VIGENCIA = {"Activacion": timedelta(hours=72), "Recuperacion": timedelta(hours=1)}


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def emitir(db, usuario_id: str, tipo: str) -> str:
    """Crea un enlace nuevo e invalida los anteriores del mismo tipo (marcándolos como usados). Devuelve el token
    en claro. Debe llamarse dentro de una transacción."""
    ahora = reloj.ahora()
    db.execute(
        "UPDATE enlace_acceso SET usado_en=? WHERE usuario_id=? AND tipo=? AND usado_en IS NULL",
        (reloj.a_texto(ahora), usuario_id, tipo),
    )
    token = secrets.token_urlsafe(32)
    db.execute(
        "INSERT INTO enlace_acceso (hash_token, usuario_id, tipo, emitido_en, vence_en) VALUES (?,?,?,?,?)",
        (hash_token(token), usuario_id, tipo, reloj.a_texto(ahora), reloj.a_texto(ahora + VIGENCIA[tipo])),
    )
    return token


def enviar_activacion(nombre: str, correo: str, token: str) -> bool:
    enlace = f"{config.FRONTEND_URL}/activar?token={token}"
    return correo_directo(
        correo,
        "ReportaYa: active su cuenta",
        f"Hola, {nombre}.\n\nLa Administración del condominio le creó una cuenta en ReportaYa.\n"
        f"Para activarla y definir su contraseña abra este enlace (vence en 72 horas y funciona una sola vez):\n\n"
        f"{enlace}\n\nSi el enlace vence, pida uno nuevo a la Administración.",
    )


def enviar_recuperacion(nombre: str, correo: str, token: str) -> bool:
    enlace = f"{config.FRONTEND_URL}/restablecer?token={token}"
    return correo_directo(
        correo,
        "ReportaYa: recupere su contraseña",
        f"Hola, {nombre}.\n\nPara definir una contraseña nueva abra este enlace "
        f"(vence en 1 hora y funciona una sola vez):\n\n{enlace}\n\n"
        f"Si usted no lo pidió, ignore este correo.",
    )


def enlace_vigente(db, token: str, tipo: str):
    """(fila del enlace, motivo del rechazo). Motivo None = el enlace sirve."""
    e = db.execute("SELECT * FROM enlace_acceso WHERE hash_token=? AND tipo=?", (hash_token(token), tipo)).fetchone()
    if not e or e["usado_en"] is not None:
        return e, "El enlace no es válido o ya se usó"
    if now_utc() > e["vence_en"]:
        return e, (
            "El enlace venció; pida uno nuevo a la Administración"
            if tipo == "Activacion"
            else "El enlace venció; solicite uno nuevo"
        )
    return e, None
