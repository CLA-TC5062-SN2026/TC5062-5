"""RF-11 y RF-14 con correo real por SMTP (servidor SMTP local de prueba, aiosmtpd)."""

import socket

import pytest
from aiosmtpd.controller import Controller

from app import correo, notificaciones, reloj
from app.correo import CorreoSMTP
from app.db import connect


class Buzon:
    def __init__(self):
        self.mensajes = []

    async def handle_DATA(self, server, session, envelope):
        self.mensajes.append((envelope.rcpt_tos, envelope.content.decode("utf-8", "replace")))
        return "250 OK"


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def smtp():
    buzon = Buzon()
    ctl = Controller(buzon, hostname="127.0.0.1", port=puerto_libre())
    ctl.start()
    correo.usar(CorreoSMTP("127.0.0.1", ctl.port, "", "", "ReportaYa <avisos@ejemplo.mx>", "ninguna"))
    yield buzon
    ctl.stop()
    correo.usar(None)


def test_alta_envia_correo_por_smtp(condo, smtp):
    folio = condo.reportar_en_unidad().json()["folio"]
    destinos = [d for rcpt, _ in smtp.mensajes for d in rcpt]
    assert "inquilino@ejemplo.com" in destinos and "admin@ejemplo.com" in destinos
    estados = {r["estado"] for r in condo.sql("SELECT estado FROM envio_correo")}
    assert estados == {"Enviado"} and any(folio in m for _, m in smtp.mensajes)


def test_activacion_por_smtp(condo, smtp):
    condo.post("admin", "/users", json={"nombre": "Nueva", "correo": "nueva@ejemplo.com", "rol": "Vigilancia"})
    assert any("nueva@ejemplo.com" in rcpt and "activar?token=" in m for rcpt, m in smtp.mensajes)


def test_servidor_caido_se_reintenta_y_queda_fallido(condo):
    correo.usar(CorreoSMTP("127.0.0.1", puerto_libre(), "", "", "avisos@ejemplo.mx", "ninguna", tiempo_limite=2))
    condo.reportar()
    for _ in range(2):
        reloj.avanzar(minutes=10)
        db = connect()
        notificaciones.procesar_correos(db)
        db.close()
    assert {(r["estado"], r["intentos"]) for r in condo.sql("SELECT estado, intentos FROM envio_correo")} == {
        ("Fallido", 3)
    }
    correo.usar(None)
