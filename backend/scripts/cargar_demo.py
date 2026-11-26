"""Datos de demostración realistas para la presentación (S11-A1): un condominio con dos torres, residentes,
personal, proveedores y ~18 reportes en todos los estados del flujo, con historial de las últimas 8 semanas.

    python scripts/cargar_demo.py          # BORRA la base configurada en .env y la carga de nuevo

Los reportes se crean con el flujo real del API (en el mismo proceso) y con el reloj del sistema fijado en
fechas pasadas (RNF-10), para que historial, avisos, tiempos y tablero sean coherentes.
Todos los usuarios tienen la contraseña «Demo1234!». Correo simulado: ver CORREO_BANDEJA_DIR.
"""

import json
import shutil
import sqlite3
import struct
import sys
import uuid
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config, reloj  # noqa: E402

PASSWORD = "Demo1234!"


def png(rgb: tuple, ancho=160, alto=120) -> bytes:
    """PNG de un color sólido, para que las fotos de la demo se vean en la interfaz."""
    fila = b"\x00" + bytes(rgb) * ancho
    crudo = zlib.compress(fila * alto)

    def bloque(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + bloque(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
        + bloque(b"IDAT", crudo)
        + bloque(b"IEND", b"")
    )


def _catalogo(db, ids: dict) -> None:
    """Las mismas categorías y subtipos que una instalación nueva (scripts/init_db.py)."""
    from scripts.init_db import CATALOGO, uid

    for nombre, prio, subs in CATALOGO:
        ids["cat:" + nombre] = uid("cat:" + nombre)
        db.execute(
            "INSERT INTO categoria (id, nombre, prioridad_sugerida) VALUES (?,?,?)",
            (ids["cat:" + nombre], nombre, prio),
        )
        db.executemany(
            "INSERT INTO subtipo (categoria_id, nombre, prioridad_sugerida) VALUES (?,?,?)",
            [(ids["cat:" + nombre], s, p) for s, p in subs],
        )


def base_de_datos(ids: dict) -> None:
    from app.security import hash_password

    if config.DATABASE_PATH.exists():
        config.DATABASE_PATH.unlink()
    shutil.rmtree(config.UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(config.CORREO_BANDEJA_DIR, ignore_errors=True)
    db = sqlite3.connect(config.DATABASE_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript((config.BASE_DIR / "db" / "esquema_bd.sql").read_text(encoding="utf-8"))
    _catalogo(db, ids)

    def nuevo(k):
        return ids.setdefault(k, str(uuid.uuid4()))

    for torre in ("A", "B"):
        for piso in range(1, 7):
            for n in ("01", "02"):
                clave = f"{torre}-{piso}{n}"
                prop = {
                    "B-502": ("Pedro Gómez", "pedro.gomez@ejemplo.mx", 0),
                    "A-301": ("Carlos Herrera", "carlos.herrera@ejemplo.mx", 1),
                }.get(clave, (f"Propietario {clave}", f"propietario.{clave.lower()}@ejemplo.mx", 1))
                db.execute("INSERT INTO ubicacion VALUES (?, 'Unidad', 1)", (nuevo(clave),))
                db.execute(
                    """INSERT INTO unidad (ubicacion_id, torre, piso, numero, propietario_nombre, propietario_correo,
                              propietario_vive_en_condominio) VALUES (?,?,?,?,?,?,?)""",
                    (ids[clave], torre, piso, f"{piso}{n}", *prop),
                )
    for nombre in (
        "Rampa del estacionamiento",
        "Alberca",
        "Elevador torre A",
        "Elevador torre B",
        "Cuarto de bombas",
        "Pasillo torre B piso 5",
        "Jardín central",
        "Portón principal",
        "Gimnasio",
    ):
        db.execute("INSERT INTO ubicacion VALUES (?, 'AreaComun', 1)", (nuevo(nombre),))
        db.execute("INSERT INTO area_comun (ubicacion_id, nombre) VALUES (?,?)", (ids[nombre], nombre))
    h = hash_password(PASSWORD)
    usuarios = [
        ("admin", "Laura Méndez", "admin@reportaya.demo", "Administracion"),
        ("auxiliar", "Sofía Ramírez", "auxiliar@reportaya.demo", "Administracion"),
        ("vigilancia", "Jorge Salas", "vigilancia@reportaya.demo", "Vigilancia"),
        ("conserje", "Ramón Torres", "mantenimiento@reportaya.demo", "Mantenimiento"),
        ("bombas", "Bombas del Norte", "bombas@reportaya.demo", "Mantenimiento"),
        ("mariana", "Mariana López", "residente@reportaya.demo", "Residente"),
        ("carlos", "Carlos Herrera", "carlos@reportaya.demo", "Residente"),
        ("ana", "Ana Torres", "ana@reportaya.demo", "Residente"),
    ]
    for k, nombre, correo, rol in usuarios:
        db.execute(
            "INSERT INTO usuario (id, nombre, correo, rol, estado_cuenta, contrasena_hash) VALUES (?,?,?,?, "
            "'Activa', ?)",
            (nuevo(k), nombre, correo, rol, h),
        )
    db.execute("INSERT INTO usuario_administracion VALUES (?, 'Administracion', 'Administrador')", (ids["admin"],))
    db.execute("INSERT INTO usuario_administracion VALUES (?, 'Administracion', 'Auxiliar')", (ids["auxiliar"],))
    db.execute("INSERT INTO vigilante (usuario_id) VALUES (?)", (ids["vigilancia"],))
    db.execute(
        "INSERT INTO usuario_mantenimiento (usuario_id, tipo, especialidad, telefono) VALUES (?, "
        "'PersonalPropio', 'Conserje', '3111234567')",
        (ids["conserje"],),
    )
    db.execute(
        "INSERT INTO usuario_mantenimiento (usuario_id, tipo, especialidad, telefono) VALUES (?, "
        "'ProveedorExterno', 'Bombas y cisterna', '3117654321')",
        (ids["bombas"],),
    )
    db.execute(
        "INSERT INTO proveedor_sin_acceso (id, nombre, especialidad, telefono) VALUES (?, 'Elevadores del "
        "Centro', 'Elevadores', '3115550000')",
        (nuevo("elevadores"),),
    )
    inicio = "2026-01-01T06:00:00Z"
    for k, unidad, ocup in (
        ("mariana", "B-502", "Inquilino"),
        ("carlos", "A-301", "Propietario"),
        ("ana", "A-402", "Inquilino"),
    ):
        db.execute("INSERT INTO residente (usuario_id) VALUES (?)", (ids[k],))
        db.execute(
            "INSERT INTO vinculacion_unidad (id, residente_id, unidad_id, ocupacion, fecha_inicio) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), ids[k], ids[unidad], ocup, inicio),
        )
    db.commit()
    db.close()


class Api:
    def __init__(self, ids):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.security import crear_token

        self.c, self.ids, self.token = TestClient(app), ids, crear_token
        self.roles = {
            "admin": "Administracion",
            "auxiliar": "Administracion",
            "vigilancia": "Vigilancia",
            "conserje": "Mantenimiento",
            "bombas": "Mantenimiento",
            "mariana": "Residente",
            "carlos": "Residente",
            "ana": "Residente",
        }

    def _h(self, quien):
        return {"Authorization": "Bearer " + self.token({"id": self.ids[quien], "rol": self.roles[quien]})}

    def ok(self, r):
        if r.status_code >= 300:
            raise RuntimeError(f"{r.request.method} {r.request.url}: {r.status_code} {r.text}")
        return r.json() if r.content else None

    def post(self, quien, ruta, **kw):
        return self.ok(self.c.post(config.API_PREFIX + ruta, headers=self._h(quien), **kw))

    def patch(self, quien, ruta, cuerpo):
        h = {**self._h(quien), "Content-Type": "application/merge-patch+json", "If-Match": "*"}
        return self.ok(self.c.patch(config.API_PREFIX + ruta, headers=h, content=json.dumps(cuerpo)))

    def put(self, quien, ruta, cuerpo):
        return self.ok(self.c.put(config.API_PREFIX + ruta, headers={**self._h(quien), "If-Match": "*"}, json=cuerpo))

    def reportar(self, quien, fotos=0, color=(70, 130, 180), **datos):
        archivos = [("fotos", (f"foto{i + 1}.png", png(color), "image/png")) for i in range(fotos)]
        return self.post(quien, "/reports", data={"datos": json.dumps(datos)}, files=archivos or None)["folio"]

    def terminar(self, quien, folio, fotos=1, **datos):
        archivos = [("fotos", (f"evidencia{i + 1}.png", png((60, 160, 90)), "image/png")) for i in range(fotos)]
        return self.post(
            quien,
            f"/reports/{folio}/completions",
            data={"datos": json.dumps(datos)} if datos else None,
            files=archivos or None,
        )


def main():
    ids: dict = {}
    base_de_datos(ids)
    api = Api(ids)
    ahora = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    def en(**d):  # «hace tanto tiempo»
        reloj.fijar(ahora - timedelta(**d))

    def U(k):
        return {"tipo": "Unidad", "unidadId": ids[k]}

    def A(k, ref=None):
        return {"tipo": "AreaComun", "areaComunId": ids[k], **({"referencia": ref} if ref else {})}

    def cat(n):
        return ids["cat:" + n]

    # 1-3. Luminaria de la rampa: tres veces en 90 días → incidencia recurrente (RF-13-AC-2)
    for dias, quien in ((52, "carlos"), (30, "ana"), (9, "mariana")):
        en(days=dias)
        f = api.reportar(
            quien,
            fotos=1,
            color=(240, 200, 60),
            categoriaId=cat("Iluminación"),
            subtipo="Pasillo o área techada",
            descripcion="La lámpara de la rampa del estacionamiento parpadea y luego se apaga",
            ubicacion=A("Rampa del estacionamiento", "Junto a la caseta"),
            esPeligroso=False,
        )
        en(days=dias, hours=-2)
        api.post(
            "admin",
            f"/reports/{f}/assignments",
            json={
                "prioridad": "Normal",
                "responsableId": ids["conserje"],
                "responsabilidad": "Comun",
                "responsableCosto": "Condominio",
            },
        )
        en(days=dias, hours=-5)
        api.post("conserje", f"/reports/{f}/cycles", json={})
        en(days=dias, hours=-20)
        api.terminar("conserje", f, notaTrabajo="Se cambió el balastro y la lámpara")
        en(days=dias, hours=-22)
        api.post("admin", f"/reports/{f}/closures", json={})
        if dias == 52:
            api.post(
                "admin",
                f"/reports/{f}/costs",
                json={"monto": 450, "pagador": "Condominio", "comentario": "Balastro y lámpara LED"},
            )

    # 4. Fuga en B-502 (inquilina; propietario no residente): reabierta y cerrada después (RF-09-AC-5)
    en(days=40)
    f = api.reportar(
        "mariana",
        fotos=2,
        color=(80, 140, 220),
        categoriaId=cat("Plomería y fugas"),
        subtipo="Fuga activa",
        descripcion="Sale agua por debajo del lavabo del baño y moja todo el piso",
        ubicacion={**U("B-502"), "parteAfectada": "Baño"},
        esPeligroso=False,
        autorizaAcceso=True,
        horariosAcceso="Lunes a viernes después de las 6 p. m.",
    )
    en(days=40, minutes=-40)
    api.post(
        "admin",
        f"/reports/{f}/assignments",
        json={
            "prioridad": "Urgente",
            "responsableId": ids["conserje"],
            "responsabilidad": "Privada",
            "responsableCosto": "Condomino",
        },
    )
    en(days=40, minutes=-55)
    api.post("conserje", f"/reports/{f}/cycles", json={})
    en(days=40, hours=-6)
    api.terminar("conserje", f, notaTrabajo="Se cambió el empaque de la llave")
    en(days=39, hours=-1)
    api.post(
        "mariana",
        f"/reports/{f}/resident-responses",
        json={"respuesta": "SigueFallando", "comentario": "Volvió a gotear en la noche"},
    )
    en(days=39, hours=-3)
    api.post("admin", f"/reports/{f}/reopenings", json={"comentario": "Se revisará de nuevo la tubería"})
    en(days=38)
    api.terminar("conserje", f, fotos=2, notaTrabajo="Se cambió el tramo de tubería bajo el lavabo")
    en(days=37)
    api.post("mariana", f"/reports/{f}/resident-responses", json={"respuesta": "YaQuedo"})
    en(days=37, hours=-1)
    api.post("admin", f"/reports/{f}/closures", json={})
    api.post(
        "admin",
        f"/reports/{f}/costs",
        json={"monto": 1200, "pagador": "Condomino", "comentario": "Tubería y mano de obra"},
    )

    # 5. Bombas: falta de agua, proveedor externo con acceso (bloque de proveedores, RF-13-AC-7)
    en(days=25)
    f = api.reportar(
        "vigilancia",
        categoriaId=cat("Bombas y cisterna"),
        subtipo="Falta de agua por falla de bombas",
        descripcion="No hay agua en la torre B desde temprano; la bomba hace ruido",
        ubicacion=A("Cuarto de bombas"),
        esPeligroso=True,
        medioOrigen="Caseta",
        fechaAviso=(ahora - timedelta(days=25, minutes=20)).isoformat(),
        nombreReferencia="Varios residentes de la torre B",
    )
    en(days=25, minutes=-10)
    api.post(
        "admin",
        f"/reports/{f}/assignments",
        json={
            "prioridad": "Urgente",
            "responsableId": ids["bombas"],
            "responsabilidad": "Comun",
            "responsableCosto": "Condominio",
        },
    )
    en(days=25, minutes=-70)
    api.post("bombas", f"/reports/{f}/cycles", json={})
    en(days=24, hours=-6)
    api.terminar("bombas", f, notaTrabajo="Se cambió el sello mecánico de la bomba 2")
    en(days=24, hours=-8)
    api.post("admin", f"/reports/{f}/closures", json={})
    api.post("admin", f"/reports/{f}/costs", json={"monto": 6800, "pagador": "Condominio"})

    # 6. Elevador torre A con proveedor sin acceso: terminado sin evidencia con justificación (RD-09)
    en(days=18)
    f = api.reportar(
        "carlos",
        categoriaId=cat("Elevador"),
        subtipo="Otra",
        descripcion="El elevador de la torre A se detiene entre pisos y tarda en abrir",
        ubicacion=A("Elevador torre A"),
        esPeligroso=False,
    )
    en(days=18, hours=-1)
    api.post(
        "admin",
        f"/reports/{f}/assignments",
        json={"prioridad": "Normal", "responsableId": ids["elevadores"], "responsabilidad": "Comun"},
    )
    en(days=17)
    api.post("admin", f"/reports/{f}/cycles", json={"comentario": "El proveedor confirmó que ya inició"})
    en(days=16)
    api.terminar(
        "admin",
        f,
        fotos=0,
        justificacionSinEvidencia="El proveedor entregó solo la orden de servicio firmada",
        garantiaVencimiento=(ahora + timedelta(days=180)).date().isoformat(),
    )
    en(days=16, hours=-1)
    api.post("admin", f"/reports/{f}/closures", json={})

    # 7. Portón principal: urgente atendido tarde (incumple el objetivo de 1 h)
    en(days=12)
    f = api.reportar(
        "vigilancia",
        categoriaId=cat("Accesos y seguridad (incluye puertas y portones)"),
        subtipo="Portón o acceso que no cierra y deja el acceso abierto",
        descripcion="El portón principal no cierra y queda abierto",
        ubicacion=A("Portón principal"),
        esPeligroso=True,
        medioOrigen="Caseta",
        fechaAviso=(ahora - timedelta(days=12)).isoformat(),
        nombreReferencia="Guardia del turno nocturno",
    )
    en(days=12, minutes=-30)
    api.post(
        "admin",
        f"/reports/{f}/assignments",
        json={"prioridad": "Urgente", "responsableId": ids["conserje"], "responsabilidad": "Comun"},
    )
    en(days=12, hours=-3)
    api.post("conserje", f"/reports/{f}/cycles", json={})
    en(days=11, hours=-6)
    api.terminar("conserje", f, notaTrabajo="Se ajustó el motor y el sensor")
    en(days=11, hours=-7)
    api.post("admin", f"/reports/{f}/closures", json={})

    # 8. Humedad en A-402: en proceso y DETENIDO por espera de pieza (RF-18)
    en(days=6)
    f = api.reportar(
        "ana",
        fotos=1,
        color=(150, 120, 90),
        categoriaId=cat("Impermeabilización"),
        descripcion="Mancha de humedad en el techo de la recámara que crece con la lluvia",
        ubicacion={**U("A-402"), "parteAfectada": "Recámara principal"},
        esPeligroso=False,
        autorizaAcceso=True,
    )
    en(days=6, hours=-3)
    api.post(
        "admin",
        f"/reports/{f}/assignments",
        json={"prioridad": "Normal", "responsableId": ids["conserje"], "responsabilidad": "PorDeterminar"},
    )
    en(days=5)
    api.post("conserje", f"/reports/{f}/cycles", json={})
    en(days=5, hours=-1)
    api.post("conserje", f"/reports/{f}/notes", json={"texto": "Viene de la azotea; falta impermeabilizante"})
    en(days=5, hours=-2)
    api.post("conserje", f"/reports/{f}/holds", json={"motivo": "EsperaDePieza"})

    # 9. Terminado hace 3 h, esperando la confirmación de Mariana (RF-09: plazo de 72 h)
    en(days=2)
    f = api.reportar(
        "mariana",
        fotos=1,
        color=(230, 120, 60),
        categoriaId=cat("Electricidad"),
        subtipo="Otra",
        descripcion="El contacto de la cocina dejó de funcionar y huele a quemado",
        ubicacion={**U("B-502"), "parteAfectada": "Cocina"},
        esPeligroso=True,
        autorizaAcceso=True,
    )
    en(days=2, minutes=-25)
    api.post(
        "admin",
        f"/reports/{f}/assignments",
        json={
            "prioridad": "Urgente",
            "responsableId": ids["conserje"],
            "responsabilidad": "Privada",
            "responsableCosto": "Condomino",
        },
    )
    en(days=2, minutes=-50)
    api.post("conserje", f"/reports/{f}/cycles", json={})
    en(hours=3)
    api.terminar("conserje", f, notaTrabajo="Se cambió el contacto y se revisó el cableado")

    # 10. Asignado con visita programada (RF-15)
    en(days=1)
    f = api.reportar(
        "carlos",
        categoriaId=cat("Albañilería y acabados"),
        subtipo="Estético",
        descripcion="Se cayeron dos azulejos de la fachada del balcón",
        ubicacion={**U("A-301"), "parteAfectada": "Balcón"},
        esPeligroso=False,
        autorizaAcceso=True,
    )
    en(hours=20)
    api.post(
        "admin",
        f"/reports/{f}/assignments",
        json={
            "prioridad": "Menor",
            "responsableId": ids["conserje"],
            "responsabilidad": "Privada",
            "responsableCosto": "Condomino",
        },
    )
    api.put("admin", f"/reports/{f}/visit", {"fechaVisita": (ahora + timedelta(days=2, hours=2)).isoformat()})

    # 11-12. Duplicado: dos residentes reportan el mismo jardín; uno se une al otro (RF-17)
    en(days=3)
    principal = api.reportar(
        "ana",
        categoriaId=cat("Jardinería"),
        descripcion="Una rama grande del jardín central está a punto de caer",
        ubicacion=A("Jardín central"),
        esPeligroso=True,
    )
    en(days=3, hours=-2)
    dup = api.reportar(
        "carlos",
        categoriaId=cat("Jardinería"),
        descripcion="Hay una rama rota colgando en el jardín central",
        ubicacion=A("Jardín central"),
        esPeligroso=True,
    )
    en(days=3, hours=-4)
    api.post("admin", f"/reports/{dup}/merges", json={"reportePrincipal": principal})
    api.post(
        "admin",
        f"/reports/{principal}/assignments",
        json={"prioridad": "Urgente", "responsableId": ids["conserje"], "responsabilidad": "Comun"},
    )

    # 13. Cancelado por la residente: ya se resolvió (RF-07-AC-6)
    en(days=4)
    f = api.reportar(
        "mariana",
        categoriaId=cat("Limpieza de áreas comunes"),
        descripcion="Basura acumulada junto al elevador de la torre B",
        ubicacion=A("Elevador torre B"),
        esPeligroso=False,
    )
    en(days=4, hours=-6)
    api.post("mariana", f"/reports/{f}/cancellations", json={"motivo": "Ya se resolvió"})

    # 14-16. Recientes sin asignar (uno capturado por WhatsApp)
    en(hours=5)
    api.reportar(
        "ana",
        fotos=1,
        color=(90, 90, 90),
        categoriaId=cat("Iluminación"),
        subtipo="Jardín o exterior",
        descripcion="Dos lámparas del andador del jardín no encienden",
        ubicacion=A("Jardín central"),
        esPeligroso=False,
    )
    en(hours=2)
    api.reportar(
        "admin",
        categoriaId=cat("Plomería y fugas"),
        subtipo="Drenaje tapado o desbordado",
        descripcion="El drenaje del gimnasio se desborda al bañarse",
        ubicacion=A("Gimnasio", "Regaderas"),
        esPeligroso=False,
        medioOrigen="WhatsApp",
        fechaAviso=(ahora - timedelta(hours=2, minutes=30)).isoformat(),
        residenteReportanteId=ids["carlos"],
    )
    en(minutes=40)
    api.reportar(
        "mariana",
        fotos=2,
        color=(200, 60, 60),
        categoriaId=cat("Electricidad"),
        subtipo="Riesgo eléctrico",
        descripcion="Cables expuestos en el pasillo del piso 5 de la torre B, cerca del registro",
        ubicacion=A("Pasillo torre B piso 5"),
        esPeligroso=True,
    )

    reloj.liberar()
    db = sqlite3.connect(config.DATABASE_PATH)
    total = db.execute("SELECT count(*) FROM reporte").fetchone()[0]
    estados = dict(db.execute("SELECT estado, count(*) FROM reporte GROUP BY estado").fetchall())
    db.close()
    print(f"Demo cargada en {config.DATABASE_PATH}: {total} reportes {estados}")
    print(
        "Usuarios (contraseña «Demo1234!»): admin@, auxiliar@, vigilancia@, mantenimiento@, bombas@, "
        "residente@ (Mariana, B-502), "
        "carlos@ (A-301), ana@ (A-402) — todos @reportaya.demo"
    )


if __name__ == "__main__":
    main()
