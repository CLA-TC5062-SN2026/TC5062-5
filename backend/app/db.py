"""Conexión a SQLite. Una conexión por petición, con las llaves foráneas activadas."""
import sqlite3
from contextlib import contextmanager

from . import config


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite lo apaga por omisión, por conexión
    return conn


def get_db():
    """Dependencia de FastAPI."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def tx(conn: sqlite3.Connection, immediate: bool = False):
    """Transacción explícita: si algo falla se revierte todo (ningún error modifica datos)."""
    conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
    try:
        yield
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
