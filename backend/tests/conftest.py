"""Entorno de las pruebas de reglas de negocio (`test_reglas.py`).

Cada prueba recibe una base de datos nueva con el **condominio de prueba del SRS (sección 3.0)**: torres A y B;
`B-502` ocupada por un inquilino con propietario no residente; `A-301` con otro residente; área común «Rampa del
estacionamiento»; Mantenimiento «Conserje» (personal propio) y «Bombas del Norte» (proveedor externo con acceso);
proveedor «Elevadores del Centro» (sin acceso); «Administrador», «Auxiliar» y «Vigilante».
El reloj del sistema se fija en cada prueba (RNF-10). El servidor corre en el mismo proceso (TestClient).
"""

import os
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="reportaya_pruebas_"))
os.environ.update(
    {
        "DATABASE_PATH": str(_TMP / "pruebas.db"),
        "UPLOAD_DIR": str(_TMP / "uploads"),
        "CORREO_BANDEJA_DIR": str(_TMP / "correos"),
        "JWT_SECRET": "secreto-solo-para-pruebas-automatizadas-0123456789",
        "TIMEZONE": "America/Mexico_City",
        "CORREO_MODO": "simulado",
        "CORREO_SIMULAR_FALLA": "0",
    }
)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import config, correo, reloj  # noqa: E402
from app.main import app  # noqa: E402
from app.security import crear_token  # noqa: E402
from scripts.init_db import CATALOGO, uid as uid_catalogo  # noqa: E402

MX = ZoneInfo("America/Mexico_City")
PASSWORD = "Prueba1234"
_HASH = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()  # costo bajo: solo pruebas
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def hora(texto: str) -> datetime:
    """'22/09/2026 10:00' en la zona del condominio."""
    return datetime.strptime(texto, "%d/%m/%Y %H:%M").replace(tzinfo=MX)


class Condominio:
    def __init__(self):
        self.ids = {}
        self.cliente = TestClient(app)

    def id(self, clave):
        return self.ids[clave]

    # --------------------------------------------------------------- sesiones
    def como(self, quien: str) -> dict:
        """Encabezados de un usuario ya activo (token firmado sin pasar por bcrypt, para que las pruebas sean rápidas)."""
        fila = {"id": self.ids[quien], "rol": self.roles[quien]}
        return {"Authorization": "Bearer " + crear_token(fila)}

    def get(self, quien, ruta, **kw):
        return self.cliente.get(config.API_PREFIX + ruta, headers={**self.como(quien), **kw.pop("headers", {})}, **kw)

    def post(self, quien, ruta, **kw):
        return self.cliente.post(config.API_PREFIX + ruta, headers={**self.como(quien), **kw.pop("headers", {})}, **kw)

    def patch(self, quien, ruta, cuerpo, etag=None):
        h = {**self.como(quien), "Content-Type": "application/merge-patch+json", "If-Match": etag or "*"}
        import json

        return self.cliente.patch(config.API_PREFIX + ruta, headers=h, content=json.dumps(cuerpo))

    def put(self, quien, ruta, cuerpo, etag="*"):
        return self.cliente.put(config.API_PREFIX + ruta, headers={**self.como(quien), "If-Match": etag}, json=cuerpo)

    # --------------------------------------------------------------- atajos del flujo
    def reportar(self, quien="inquilino", fotos=(), video=None, **campos):
        import json

        datos = {
            "categoriaId": self.cat("Iluminación"),
            "subtipo": "Pasillo o área techada",
            "descripcion": "Lámpara parpadeando cerca de la entrada",
            "ubicacion": {"tipo": "AreaComun", "areaComunId": self.id("rampa")},
            "esPeligroso": False,
        }
        datos.update(campos)
        datos = {k: v for k, v in datos.items() if v is not ...}
        archivos = [("fotos", f) for f in fotos] + ([("video", video)] if video else [])
        return self.post(quien, "/reports", data={"datos": json.dumps(datos)}, files=archivos or None)

    def reportar_en_unidad(self, quien="inquilino", unidad="B-502", **campos):
        base = {
            "categoriaId": self.cat("Plomería y fugas"),
            "subtipo": "Fuga activa",
            "descripcion": "Fuga de agua bajo el lavabo",
            "ubicacion": {"tipo": "Unidad", "unidadId": self.id(unidad), "parteAfectada": "Baño"},
            "autorizaAcceso": True,
        }
        base.update(campos)
        return self.reportar(quien, **base)

    def asignar(self, folio, responsable="conserje", prioridad="Urgente", quien="admin", **extra):
        return self.post(
            quien,
            f"/reports/{folio}/assignments",
            json={"prioridad": prioridad, "responsableId": self.id(responsable), **extra},
        )

    def iniciar(self, folio, quien="conserje", **cuerpo):
        return self.post(quien, f"/reports/{folio}/cycles", json=cuerpo)

    def terminar(self, folio, quien="conserje", fotos=1, datos=None):
        import json

        archivos = [("fotos", (f"e{i}.png", PNG, "image/png")) for i in range(fotos)]
        return self.post(
            quien,
            f"/reports/{folio}/completions",
            data={"datos": json.dumps(datos)} if datos else None,
            files=archivos or None,
        )

    def hasta_terminado(self, folio, responsable="conserje"):
        assert self.asignar(folio, responsable).status_code == 201
        quien = "admin" if responsable == "elevadores" else responsable
        assert self.iniciar(folio, quien).status_code == 201
        r = (
            self.terminar(folio, quien)
            if responsable != "elevadores"
            else self.terminar(folio, "admin", fotos=0, datos={"justificacionSinEvidencia": "Orden firmada"})
        )
        assert r.status_code == 201, r.text
        return r

    def cat(self, nombre):
        return uid_catalogo("cat:" + nombre)

    def sql(self, q, *p):
        import sqlite3

        c = sqlite3.connect(config.DATABASE_PATH)
        c.row_factory = sqlite3.Row
        filas = c.execute(q, p).fetchall()
        c.commit()
        c.close()
        return filas

    def correos_a(self, destinatario):
        return [
            p.read_text(encoding="utf-8")
            for p in sorted(config.CORREO_BANDEJA_DIR.glob("*.txt"))
            if f"Para: {destinatario}" in p.read_text(encoding="utf-8")
        ]


def _sembrar(db, c: Condominio):
    db.executescript((config.BASE_DIR / "db" / "esquema_bd.sql").read_text(encoding="utf-8"))
    for nombre, prio, subs in CATALOGO:
        db.execute(
            "INSERT INTO categoria (id, nombre, prioridad_sugerida) VALUES (?,?,?)",
            (uid_catalogo("cat:" + nombre), nombre, prio),
        )
        for s, p in subs:
            db.execute(
                "INSERT INTO subtipo (categoria_id, nombre, prioridad_sugerida) VALUES (?,?,?)",
                (uid_catalogo("cat:" + nombre), s, p),
            )
    nid = lambda k: c.ids.setdefault(k, str(uuid.uuid4()))
    unidades = [
        ("B-502", "B", 5, "502", "Pedro Propietario", "pedro.propietario@ejemplo.com", 0),
        ("A-301", "A", 3, "301", "Alicia Dueña", "alicia@ejemplo.com", 1),
        ("A-402", "A", 4, "402", "Óscar Dueño", "oscar@ejemplo.com", 0),
        ("A-502", "A", 5, "502", "Elena Dueña", "elena@ejemplo.com", 0),
        ("B-401", "B", 4, "401", "Bruno Dueño", "bruno@ejemplo.com", 0),
    ]
    for k, torre, piso, numero, pn, pc, vive in unidades:
        db.execute("INSERT INTO ubicacion VALUES (?, 'Unidad', 1)", (nid(k),))
        db.execute(
            """INSERT INTO unidad (ubicacion_id, torre, piso, numero, propietario_nombre, propietario_correo,
                      propietario_vive_en_condominio) VALUES (?,?,?,?,?,?,?)""",
            (c.ids[k], torre, piso, numero, pn, pc, vive),
        )
    for k, nombre in (("rampa", "Rampa del estacionamiento"), ("alberca", "Alberca")):
        db.execute("INSERT INTO ubicacion VALUES (?, 'AreaComun', 1)", (nid(k),))
        db.execute("INSERT INTO area_comun (ubicacion_id, nombre) VALUES (?,?)", (c.ids[k], nombre))
    usuarios = [
        ("admin", "Administrador", "admin@ejemplo.com", "Administracion"),
        ("auxiliar", "Auxiliar", "auxiliar@ejemplo.com", "Administracion"),
        ("vigilante", "Vigilante", "vigilante@ejemplo.com", "Vigilancia"),
        ("conserje", "Conserje", "conserje@ejemplo.com", "Mantenimiento"),
        ("bombas", "Bombas del Norte", "bombas@ejemplo.com", "Mantenimiento"),
        ("inquilino", "Inquilino de B-502", "inquilino@ejemplo.com", "Residente"),
        ("residente_a301", "Residente de A-301", "a301@ejemplo.com", "Residente"),
    ]
    c.roles = {}
    for k, nombre, correo_, rol in usuarios:
        db.execute(
            "INSERT INTO usuario (id, nombre, correo, rol, estado_cuenta, contrasena_hash) VALUES (?,?,?,?, 'Activa', ?)",
            (nid(k), nombre, correo_, rol, _HASH),
        )
        c.roles[k] = rol
    db.execute("INSERT INTO usuario_administracion VALUES (?, 'Administracion', 'Administrador')", (c.ids["admin"],))
    db.execute("INSERT INTO usuario_administracion VALUES (?, 'Administracion', 'Auxiliar')", (c.ids["auxiliar"],))
    db.execute("INSERT INTO vigilante (usuario_id) VALUES (?)", (c.ids["vigilante"],))
    db.execute(
        "INSERT INTO usuario_mantenimiento (usuario_id, tipo, especialidad) VALUES (?, 'PersonalPropio', 'Conserje')",
        (c.ids["conserje"],),
    )
    db.execute(
        "INSERT INTO usuario_mantenimiento (usuario_id, tipo, especialidad, telefono) VALUES (?, 'ProveedorExterno', 'Bombas y cisterna', '4431112233')",
        (c.ids["bombas"],),
    )
    db.execute(
        "INSERT INTO proveedor_sin_acceso (id, nombre, especialidad, telefono) VALUES (?, 'Elevadores del Centro', 'Elevadores', '4434445566')",
        (nid("elevadores"),),
    )
    for k, unidad, ocup in (("inquilino", "B-502", "Inquilino"), ("residente_a301", "A-301", "Propietario")):
        db.execute("INSERT INTO residente (usuario_id) VALUES (?)", (c.ids[k],))
        db.execute(
            "INSERT INTO vinculacion_unidad (id, residente_id, unidad_id, ocupacion, fecha_inicio) VALUES (?,?,?,?, '2026-01-01T06:00:00Z')",
            (str(uuid.uuid4()), c.ids[k], c.ids[unidad], ocup),
        )
    db.commit()


@pytest.fixture
def condo():
    import shutil
    import sqlite3

    for p in (config.DATABASE_PATH,):
        if p.exists():
            p.unlink()
    shutil.rmtree(config.UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(config.CORREO_BANDEJA_DIR, ignore_errors=True)
    c = Condominio()
    db = sqlite3.connect(config.DATABASE_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    _sembrar(db, c)
    db.close()
    reloj.fijar(hora("21/09/2026 09:00"))
    correo.usar(None)
    yield c
    reloj.liberar()
    correo.usar(None)
