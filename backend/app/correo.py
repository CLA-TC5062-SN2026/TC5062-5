"""Servicio de correo intercambiable (SRS 3.4: interfaz de software «servicio de correo»).

Los casos de uso dependen de la interfaz `ServicioCorreo`, no de una implementación concreta:
- `CORREO_MODO=simulado` → `CorreoSimulado`: cada correo queda como archivo .txt en `CORREO_BANDEJA_DIR` (demo).
- `CORREO_MODO=smtp` → `CorreoSMTP`: envío real por SMTP (Gmail con contraseña de aplicación, Outlook, SendGrid...).
Las reglas de RF-11 (reintentos, «Fallido») y RF-14 no cambian con la implementación.
"""

import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol

from . import config, reloj


class CorreoNoEnviado(Exception):
    """El servicio de correo no respondió o rechazó el envío."""


class ServicioCorreo(Protocol):
    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        """Envía el correo o lanza `CorreoNoEnviado`."""


class CorreoSimulado:
    def __init__(self, carpeta: Path, simular_falla: bool = False):
        self.carpeta = carpeta
        self.simular_falla = simular_falla

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        if self.simular_falla:
            raise CorreoNoEnviado("Servicio de correo simulado sin respuesta (CORREO_SIMULAR_FALLA=1)")
        self.carpeta.mkdir(parents=True, exist_ok=True)
        marca = reloj.ahora().strftime("%Y%m%d-%H%M%S")
        seguro = re.sub(r"[^A-Za-z0-9@._-]", "_", destinatario)
        n = len(list(self.carpeta.glob(f"{marca}_*"))) + 1
        archivo = self.carpeta / f"{marca}_{n:03d}_{seguro}.txt"
        archivo.write_text(f"Para: {destinatario}\nAsunto: {asunto}\n\n{cuerpo}\n", encoding="utf-8")


class CorreoSMTP:
    def __init__(
        self,
        host: str,
        puerto: int,
        usuario: str,
        contrasena: str,
        remitente: str,
        seguridad: str = "starttls",
        tiempo_limite: int = 15,
    ):
        if not host or not remitente:
            raise RuntimeError("Con CORREO_MODO=smtp defina SMTP_HOST y SMTP_REMITENTE en .env")
        if seguridad not in ("starttls", "ssl", "ninguna"):
            raise RuntimeError("SMTP_SEGURIDAD debe ser starttls, ssl o ninguna")
        self.host, self.puerto, self.usuario, self.contrasena = host, puerto, usuario, contrasena
        self.remitente, self.seguridad, self.tiempo_limite = remitente, seguridad, tiempo_limite

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.remitente, destinatario, asunto
        msg.set_content(cuerpo)
        try:
            if self.seguridad == "ssl":
                conexion = smtplib.SMTP_SSL(
                    self.host, self.puerto, timeout=self.tiempo_limite, context=ssl.create_default_context()
                )
            else:
                conexion = smtplib.SMTP(self.host, self.puerto, timeout=self.tiempo_limite)
            with conexion as smtp:
                if self.seguridad == "starttls":
                    smtp.starttls(context=ssl.create_default_context())
                if self.usuario:
                    smtp.login(self.usuario, self.contrasena)
                smtp.send_message(msg)
        except (
            smtplib.SMTPException,
            OSError,
        ) as exc:  # sin respuesta, rechazo o credenciales: se reintenta (RF-11-AC-4)
            raise CorreoNoEnviado(str(exc)) from exc


_servicio: ServicioCorreo | None = None


def servicio() -> ServicioCorreo:
    global _servicio
    if _servicio is None:
        if config.CORREO_MODO == "simulado":
            _servicio = CorreoSimulado(config.CORREO_BANDEJA_DIR, config.CORREO_SIMULAR_FALLA)
        elif config.CORREO_MODO == "smtp":
            _servicio = CorreoSMTP(
                config.SMTP_HOST,
                config.SMTP_PUERTO,
                config.SMTP_USUARIO,
                config.SMTP_CONTRASENA,
                config.SMTP_REMITENTE,
                config.SMTP_SEGURIDAD,
            )
        else:
            raise RuntimeError(f"CORREO_MODO={config.CORREO_MODO!r} no es válido: use 'simulado' o 'smtp'")
    return _servicio


def usar(otro: ServicioCorreo | None) -> None:
    """Sustituye el servicio (pruebas). None vuelve al configurado."""
    global _servicio
    _servicio = otro
