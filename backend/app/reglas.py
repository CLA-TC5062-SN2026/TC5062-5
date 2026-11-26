"""Reglas de negocio compartidas: flujo de estados (RF-07, patrón State del SRS 4), historial, parámetros (RF-27)
y permisos de gestión de la Administración (RD-10, RF-21)."""

from datetime import timedelta

from . import reloj
from .security import ADMIN, UsuarioSesion
from .util import conflicto, new_id, no_encontrado, now_utc, prohibido

ESTADOS_FINALES = ("Cancelado", "Unido")

# RF-07: solo estas transiciones. Quién puede hacer cada una lo decide el endpoint (PERMISOS + reglas propias).
TRANSICIONES = {
    ("Reportado", "Asignado"),
    ("Reportado", "Cancelado"),
    ("Asignado", "Cancelado"),
    ("Reportado", "Unido"),
    ("Asignado", "Unido"),
    ("Asignado", "EnProceso"),
    ("EnProceso", "Terminado"),
    ("Terminado", "Cerrado"),
    ("Terminado", "EnProceso"),  # reapertura desde Terminado (RF-09-AC-5)
    ("Cerrado", "EnProceso"),  # reapertura de un cerrado (RF-19)
}


def exigir_transicion(r, nuevo: str, mensaje: str = "Transición no permitida") -> None:
    if (r["estado"], nuevo) not in TRANSICIONES:
        raise conflicto(mensaje)


def obtener_reporte(db, folio: str):
    r = db.execute("SELECT * FROM reporte WHERE folio=?", (folio,)).fetchone()
    if not r:
        raise no_encontrado("Reporte no encontrado")
    return r


def historial(db, folio, autor_id, tipo, campo=None, anterior=None, nuevo=None, comentario=None) -> str:
    eid = new_id()
    db.execute(
        """INSERT INTO entrada_historial (id, reporte_folio, fecha, tipo, campo, valor_anterior, valor_nuevo,
                  comentario, autor_id) VALUES (?,?,?,?,?,?,?,?,?)""",
        (eid, folio, now_utc(), tipo, campo, anterior, nuevo, comentario, autor_id),
    )
    return eid


def registrar_cambio_estado(
    db, folio: str, anterior: str, nuevo: str, autor_id: str, comentario=None, en_nombre_de=None
) -> str:
    """Cada transición guarda estado anterior y nuevo, usuario, fecha, comentario y, si aplica, el proveedor sin
    acceso en cuyo nombre se registró (RF-07)."""
    eid = historial(db, folio, autor_id, "CambioEstado", comentario=comentario)
    db.execute(
        """INSERT INTO cambio_estado (entrada_id, estado_anterior, estado_nuevo, actua_en_nombre_de_id)
                  VALUES (?,?,?,?)""",
        (eid, anterior, nuevo, en_nombre_de),
    )
    return eid


def reclasificacion(db, folio, autor_id, campo, anterior, nuevo, comentario=None) -> None:
    eid = historial(
        db, folio, autor_id, "Reclasificacion", campo, anterior, nuevo if nuevo is not None else "—", comentario
    )
    db.execute("INSERT INTO reclasificacion (entrada_id) VALUES (?)", (eid,))


# ----------------------------------------------------------------- parámetros (RF-27)
def parametro(db, clave: str) -> float:
    return db.execute("SELECT valor FROM parametro WHERE clave=?", (clave,)).fetchone()["valor"]


def mas_horas(horas: float) -> str:
    return reloj.a_texto(reloj.ahora() + timedelta(hours=horas))


# ----------------------------------------------------------------- ciclos de atención
def ciclo_actual(db, folio: str):
    return db.execute(
        "SELECT * FROM ciclo_atencion WHERE reporte_folio=? ORDER BY numero DESC LIMIT 1", (folio,)
    ).fetchone()


def abrir_ciclo(db, folio: str) -> int:
    n = db.execute(
        "SELECT COALESCE(MAX(numero), 0) + 1 FROM ciclo_atencion WHERE reporte_folio=?", (folio,)
    ).fetchone()[0]
    db.execute("INSERT INTO ciclo_atencion (reporte_folio, numero, inicio) VALUES (?,?,?)", (folio, n, now_utc()))
    return n


# ----------------------------------------------------------------- gestión de la Administración (RD-10, RF-21)
def perfil_administracion(db, usuario_id: str):
    f = db.execute(
        "SELECT perfil_administracion FROM usuario_administracion WHERE usuario_id=?", (usuario_id,)
    ).fetchone()
    return f["perfil_administracion"] if f else None


def delegacion_vigente(db, auxiliar_id: str) -> bool:
    ahora = now_utc()
    return (
        db.execute(
            """SELECT 1 FROM delegacion WHERE auxiliar_id=? AND habilitada=1 AND fecha_inicio <= ?
                         AND (fecha_fin IS NULL OR fecha_fin > ?)""",
            (auxiliar_id, ahora, ahora),
        ).fetchone()
        is not None
    )


def exigir_gestion(db, quien: UsuarioSesion) -> None:
    """Asignar, reclasificar, cerrar y decidir la reapertura: la Administración; la Auxiliar solo con una
    delegación vigente (RF-21-AC-2, AC-3, AC-5)."""
    if quien.rol != ADMIN:
        raise prohibido()
    if perfil_administracion(db, quien.id) == "Auxiliar" and not delegacion_vigente(db, quien.id):
        raise prohibido("La Auxiliar necesita una delegación vigente del Administrador (RF-21)")


def es_responsable(r, usuario_id: str) -> bool:
    return r["responsable_usuario_id"] == usuario_id
