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

# ---------------------------------------------------------------- autenticación (S05-S06-A2)
# El secreto NUNCA va en el código: si falta o es corto, la aplicación no arranca.
JWT_SECRET = os.getenv("JWT_SECRET", "")
if len(JWT_SECRET) < 32 or JWT_SECRET.startswith("cambie-este-valor"):
    raise RuntimeError("Defina JWT_SECRET en .env con un valor aleatorio propio de al menos 32 caracteres (ver .env.example)")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "30"))  # minutos de vigencia del token (RNF-06)
if JWT_EXPIRATION <= 0:
    raise RuntimeError("JWT_EXPIRATION debe ser un número de minutos mayor que cero")
