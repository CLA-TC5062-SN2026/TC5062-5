"""Configuración leída de variables de entorno (archivo .env, ver .env.example)."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _path(valor: str) -> Path:
    p = Path(valor)
    return p if p.is_absolute() else (BASE_DIR / p)


DATABASE_PATH = _path(os.getenv("DATABASE_PATH", "./reportaya.db"))
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "America/Mexico_City"))
UPLOAD_DIR = _path(os.getenv("UPLOAD_DIR", "./uploads"))
MAX_FOTO_BYTES = int(os.getenv("MAX_FOTO_MB", "10")) * 1024 * 1024
MAX_VIDEO_BYTES = int(os.getenv("MAX_VIDEO_MB", "50")) * 1024 * 1024
