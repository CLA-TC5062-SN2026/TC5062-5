"""Reloj del sistema (RNF-10).

Toda regla que depende del tiempo (plazos de RF-09, RF-14 y RF-19, vencimientos de RF-13, reintentos de
correo de RF-11) pide la hora a este módulo. Las pruebas automatizadas la fijan con `fijar()` y la liberan
con `liberar()`; en producción siempre es la hora real en UTC.
"""

from datetime import datetime, timedelta, timezone

_fija: datetime | None = None


def ahora() -> datetime:
    """Hora actual en UTC, sin microsegundos (la BD guarda segundos)."""
    base = _fija if _fija is not None else datetime.now(timezone.utc)
    return base.replace(microsecond=0)


def fijar(momento: datetime) -> None:
    global _fija
    if momento.tzinfo is None:
        raise ValueError("La hora fijada debe incluir zona horaria")
    _fija = momento.astimezone(timezone.utc)


def avanzar(**delta) -> None:
    """Adelanta la hora fijada (solo pruebas): avanzar(hours=73)."""
    if _fija is None:
        raise RuntimeError("Primero fije la hora con fijar()")
    fijar(_fija + timedelta(**delta))


def liberar() -> None:
    global _fija
    _fija = None


FORMATO = "%Y-%m-%dT%H:%M:%SZ"


def a_texto(momento: datetime) -> str:
    return momento.astimezone(timezone.utc).strftime(FORMATO)


def de_texto(valor: str) -> datetime:
    return datetime.strptime(valor, FORMATO).replace(tzinfo=timezone.utc)
