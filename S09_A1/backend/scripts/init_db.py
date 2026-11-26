"""Crea la base de datos SQLite con db/esquema_bd.sql y carga el catálogo RD-01 del SRS.

    python scripts/init_db.py            # crea la BD si no existe
    python scripts/init_db.py --reset    # la borra y la crea de nuevo
    python scripts/init_db.py --demo     # además carga usuarios, una unidad y avisos de ejemplo
"""
import argparse
import sqlite3
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config  # noqa: E402

NS = uuid.UUID("6f0d3c7e-2b1a-4a55-9d0e-7a5f3c2b1e90")
uid = lambda nombre: str(uuid.uuid5(NS, nombre))

# RD-01 — (categoría, prioridad si no tiene subtipos, [(subtipo, prioridad)])
CATALOGO = [
    ("Plomería y fugas", None, [("Fuga activa", "Urgente"), ("Drenaje tapado o desbordado", "Urgente"), ("Otra", "Normal")]),
    ("Electricidad", None, [("Riesgo eléctrico", "Urgente"), ("Otra", "Normal")]),
    ("Iluminación", None, [("Pasillo o área techada", "Normal"), ("Jardín o exterior", "Menor")]),
    ("Bombas y cisterna", None, [("Falta de agua por falla de bombas", "Urgente"), ("Otra", "Normal")]),
    ("Elevador", None, [("Persona atrapada", "Urgente"), ("Otra", "Normal")]),
    ("Accesos y seguridad (incluye puertas y portones)", None,
     [("Portón o acceso que no cierra y deja el acceso abierto", "Urgente"), ("Otra", "Normal")]),
    ("Albañilería y acabados", None, [("Daño con riesgo de caída o accidente", "Urgente"), ("Estético", "Menor"), ("Otra", "Normal")]),
    ("Impermeabilización", "Normal", []),
    ("Limpieza de áreas comunes", "Normal", []),
    ("Jardinería", "Normal", []),
    ("Otro", "Normal", []),
]
T = "2026-01-01T12:00:00Z"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    ruta = config.DATABASE_PATH
    if a.reset and ruta.exists():
        ruta.unlink()
    existia = ruta.exists()
    conn = sqlite3.connect(ruta)
    conn.execute("PRAGMA foreign_keys = ON")
    if not existia:
        conn.executescript((config.BASE_DIR / "db" / "esquema_bd.sql").read_text(encoding="utf-8"))
        for nombre, prio, subs in CATALOGO:
            conn.execute("INSERT INTO categoria (id, nombre, prioridad_sugerida) VALUES (?,?,?)", (uid("cat:" + nombre), nombre, prio))
            for s, p in subs:
                conn.execute("INSERT INTO subtipo (categoria_id, nombre, prioridad_sugerida) VALUES (?,?,?)", (uid("cat:" + nombre), s, p))
        conn.commit()
        print(f"Base creada: {ruta}")
    else:
        print(f"La base ya existe: {ruta} (use --reset para recrearla)")
    if a.demo:
        demo(conn)
    print("Tablas:", conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0])
    conn.close()


PASSWORD_DEMO = "Demo1234!"  # solo para datos de ejemplo locales


def demo(conn):
    if conn.execute("SELECT 1 FROM usuario LIMIT 1").fetchone():
        print("Ya hay usuarios; no se cargan datos de ejemplo.")
        return
    usuarios = [("admin", "Ana Administradora", "admin@reportaya.demo", "Administracion"),
                ("aux", "Aurora Auxiliar", "auxiliar@reportaya.demo", "Administracion"),
                ("vig", "Víctor Vigilante", "vigilancia@reportaya.demo", "Vigilancia"),
                ("mant", "Mateo Mantenimiento", "mantenimiento@reportaya.demo", "Mantenimiento"),
                ("res", "Rosa Residente", "residente@reportaya.demo", "Residente")]
    from app.security import hash_password
    h = hash_password(PASSWORD_DEMO)  # bcrypt real (antes: 'hash-demo', con el que nadie podía iniciar sesión)
    for k, nombre, correo, rol in usuarios:
        conn.execute("INSERT INTO usuario (id, nombre, correo, rol, estado_cuenta, contrasena_hash) VALUES (?,?,?,?, 'Activa', ?)",
                     (uid("u:" + k), nombre, correo, rol, h))
    conn.execute("INSERT INTO usuario_administracion VALUES (?, 'Administracion', 'Administrador')", (uid("u:admin"),))
    conn.execute("INSERT INTO usuario_administracion VALUES (?, 'Administracion', 'Auxiliar')", (uid("u:aux"),))
    conn.execute("INSERT INTO vigilante (usuario_id) VALUES (?)", (uid("u:vig"),))
    conn.execute("INSERT INTO usuario_mantenimiento (usuario_id, tipo, especialidad) VALUES (?, 'PersonalPropio', 'Conserje')", (uid("u:mant"),))
    conn.execute("INSERT INTO residente (usuario_id) VALUES (?)", (uid("u:res"),))
    conn.execute("INSERT INTO ubicacion VALUES (?, 'Unidad', 1)", (uid("unidad:B-502"),))
    conn.execute("""INSERT INTO unidad (ubicacion_id, torre, piso, numero, propietario_nombre, propietario_correo,
                    propietario_vive_en_condominio) VALUES (?, 'B', 5, '502', 'Pedro Propietario', 'pedro@example.com', 0)""", (uid("unidad:B-502"),))
    conn.execute("INSERT INTO ubicacion VALUES (?, 'AreaComun', 1)", (uid("area:Alberca"),))
    conn.execute("INSERT INTO area_comun (ubicacion_id, nombre) VALUES (?, 'Alberca')", (uid("area:Alberca"),))
    conn.execute("INSERT INTO vinculacion_unidad (id, residente_id, unidad_id, ocupacion, fecha_inicio) VALUES (?,?,?, 'Inquilino', ?)",
                 (uid("vinc:res"), uid("u:res"), uid("unidad:B-502"), T))
    # Un reporte con un aviso y un correo pendiente, para que las consultas de avisos tengan datos.
    conn.execute("""INSERT INTO reporte (folio, fecha_aviso, fecha_captura, medio_origen, descripcion, es_peligroso, estado,
                    prioridad_sugerida, ubicacion_id, reportante_id, capturado_por, categoria_id, subtipo_nombre, autoriza_acceso)
                    VALUES ('RY-000001', ?, ?, 'Sistema', 'Fuga de agua bajo el fregadero de la cocina', 0, 'Reportado',
                    'Urgente', ?, ?, ?, ?, 'Fuga activa', 1)""",
                 (T, T, uid("unidad:B-502"), uid("u:res"), uid("u:res"), uid("cat:Plomería y fugas")))
    conn.execute("INSERT INTO entrada_historial (id, reporte_folio, fecha, tipo, autor_id) VALUES (?, 'RY-000001', ?, 'CambioEstado', ?)",
                 (uid("h:1"), T, uid("u:res")))
    conn.execute("INSERT INTO cambio_estado (entrada_id, estado_anterior, estado_nuevo) VALUES (?, NULL, 'Reportado')", (uid("h:1"),))
    conn.execute("INSERT INTO aviso (id, tipo, reporte_folio, evento, fecha) VALUES (?, 'Sistema', 'RY-000001', 'ReporteCreado', ?)", (uid("av:1"), T))
    conn.execute("INSERT INTO aviso_sistema (aviso_id, destinatario_usuario_id, mensaje) VALUES (?,?, 'Nuevo reporte RY-000001: Plomería y fugas')",
                 (uid("av:1"), uid("u:admin")))
    conn.execute("INSERT INTO aviso (id, tipo, reporte_folio, evento, fecha) VALUES (?, 'Correo', 'RY-000001', 'ReporteCreado', ?)", (uid("av:2"), T))
    conn.execute("INSERT INTO envio_correo (aviso_id, destinatario) VALUES (?, 'pedro@example.com')", (uid("av:2"),))
    conn.commit()
    print("Datos de ejemplo cargados. Usuarios *@reportaya.demo (admin, auxiliar, vigilancia, mantenimiento, residente)"
          f" con contraseña {PASSWORD_DEMO!r}. Unidad B-502: {uid('unidad:B-502')}")


if __name__ == "__main__":
    main()
