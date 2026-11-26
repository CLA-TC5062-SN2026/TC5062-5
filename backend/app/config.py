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
# Almacén de fotos y videos (RNF-08): «local» (UPLOAD_DIR) o «s3» (AWS S3, Cloudflare R2, MinIO...).
ALMACEN = os.getenv("ALMACEN", "local")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PREFIJO = os.getenv("S3_PREFIJO", "reportaya")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")  # vacío = AWS; R2: https://<cuenta>.r2.cloudflarestorage.com
S3_REGION = os.getenv("S3_REGION", "")
MAX_FOTO_BYTES = int(os.getenv("MAX_FOTO_MB", "10")) * 1024 * 1024
MAX_VIDEO_BYTES = int(os.getenv("MAX_VIDEO_MB", "50")) * 1024 * 1024

# ---------------------------------------------------------------- correo (RF-11, RF-14)
# CORREO_MODO=simulado: no sale a internet; cada correo se escribe como archivo .txt en CORREO_BANDEJA_DIR
# (ahí se ven los enlaces de activación en la demo). CORREO_SIMULAR_FALLA=1 simula que el servicio no responde
# (RF-11-AC-4: 3 intentos y estado «Fallido»).
CORREO_MODO = os.getenv("CORREO_MODO", "simulado")
CORREO_BANDEJA_DIR = _path(os.getenv("CORREO_BANDEJA_DIR", "./correos"))
CORREO_SIMULAR_FALLA = os.getenv("CORREO_SIMULAR_FALLA", "0") == "1"
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PUERTO = int(os.getenv("SMTP_PUERTO", "587"))
SMTP_USUARIO = os.getenv("SMTP_USUARIO", "")
SMTP_CONTRASENA = os.getenv("SMTP_CONTRASENA", "")
SMTP_REMITENTE = os.getenv("SMTP_REMITENTE", "")  # p. ej. "ReportaYa <avisos@su-condominio.mx>"
SMTP_SEGURIDAD = os.getenv("SMTP_SEGURIDAD", "starttls")  # starttls (587) · ssl (465) · ninguna (solo pruebas)
CORREO_REINTENTO_MINUTOS = int(os.getenv("CORREO_REINTENTO_MINUTOS", "10"))
CORREO_REVISION_SEGUNDOS = int(os.getenv("CORREO_REVISION_SEGUNDOS", "60"))
# URL del frontend, para armar los enlaces de activación y recuperación que van en el correo.
# Base de los enlaces de los correos; en Render, la URL pública del servicio si no se define.
FRONTEND_URL = os.getenv("FRONTEND_URL", os.getenv("RENDER_EXTERNAL_URL", "http://localhost:5173")).rstrip("/")
# Carpeta con la SPA compilada (frontend/dist). Solo en el despliegue de un contenedor (Render); vacío = no se sirve.
FRONTEND_DIST = _path(os.environ["FRONTEND_DIST"]) if os.getenv("FRONTEND_DIST") else None

# ---------------------------------------------------------------- autenticación (S05-S06-A2)
# El secreto NUNCA va en el código: si falta o es corto, la aplicación no arranca.
JWT_SECRET = os.getenv("JWT_SECRET", "")
if len(JWT_SECRET) < 32 or JWT_SECRET.startswith("cambie-este-valor"):
    raise RuntimeError(
        "Defina JWT_SECRET en .env con un valor aleatorio propio de al menos 32 caracteres (ver .env.example)"
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "30"))  # minutos de vigencia del token (RNF-06)
if JWT_EXPIRATION <= 0:
    raise RuntimeError("JWT_EXPIRATION debe ser un número de minutos mayor que cero")
