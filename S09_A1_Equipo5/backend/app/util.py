"""Utilidades comunes: errores del contrato (esquema Error), fechas, ETag, paginación."""
import hashlib
import json
import re
import uuid
from datetime import date, datetime, time, timezone
from typing import Any

from fastapi import Query
from fastapi.responses import JSONResponse

from . import config

UUID_RE = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
FOLIO_RE = r"^RY-\d{6}$"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ApiError(Exception):
    """Error con el formato del esquema `Error` del openapi_equipo.yaml."""

    def __init__(self, status: int, codigo: str, mensaje: str, errores: list[dict] | None = None):
        self.status, self.codigo, self.mensaje, self.errores = status, codigo, mensaje, errores


def no_encontrado(msg: str = "Recurso no encontrado") -> ApiError:
    return ApiError(404, "NO_ENCONTRADO", msg)


def prohibido(msg: str = "No tiene permiso para esta acción") -> ApiError:
    return ApiError(403, "PROHIBIDO", msg)


def conflicto(msg: str, codigo: str = "TRANSICION_NO_PERMITIDA") -> ApiError:
    return ApiError(409, codigo, msg)


def peticion_invalida(msg: str = "La petición no es válida") -> ApiError:
    return ApiError(400, "PETICION_INVALIDA", msg)


def validacion(campo: str, mensaje: str) -> ApiError:
    return ApiError(422, "VALIDACION", "Datos inválidos", [{"campo": campo, "mensaje": mensaje}])


# ---------------------------------------------------------------- fechas
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_utc(valor: str, campo: str) -> str:
    """ISO 8601 (con o sin zona; sin zona se toma la del condominio) -> UTC 'YYYY-MM-DDTHH:MM:SSZ'."""
    try:
        dt = datetime.fromisoformat(valor.strip().replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise validacion(campo, "Fecha y hora no válida (use ISO 8601)")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=config.TIMEZONE)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def out_dt(valor: str | None) -> str | None:
    """UTC de la BD -> ISO 8601 en la zona horaria del condominio."""
    if valor is None:
        return None
    dt = datetime.strptime(valor, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.astimezone(config.TIMEZONE).isoformat(timespec="seconds")


def day_start_utc(d: date) -> str:
    return datetime.combine(d, time.min, config.TIMEZONE).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def day_end_utc(d: date) -> str:
    return datetime.combine(d, time(23, 59, 59), config.TIMEZONE).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- respuestas
def new_id() -> str:
    return str(uuid.uuid4())


def compactar(obj: Any) -> Any:
    """Quita las claves con valor None (los campos opcionales del API se omiten)."""
    if isinstance(obj, dict):
        return {k: compactar(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [compactar(v) for v in obj]
    return obj


def etag_de(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return '"' + hashlib.sha1(raw.encode()).hexdigest()[:32] + '"'


def responder(data: Any, status: int = 200, location: str | None = None, etag: bool = False,
              etag_de_recurso: Any = None) -> JSONResponse:
    """JSON de respuesta. `etag_de_recurso` permite calcular el ETag sobre el recurso aunque la
    respuesta lleve campos extra (p. ej. archivosRechazados en el alta de un reporte)."""
    data = compactar(data)
    headers = {}
    if location:
        headers["Location"] = config.API_PREFIX + location
    if etag:
        headers["ETag"] = etag_de(compactar(etag_de_recurso) if etag_de_recurso is not None else data)
    return JSONResponse(content=data, status_code=status, headers=headers)


def verificar_if_match(if_match: str, actual: Any) -> None:
    """If-Match (RFC 9110): 412 si no coincide con el ETag vigente."""
    vigente = etag_de(compactar(actual))
    candidatos = [c.strip().removeprefix("W/") for c in if_match.split(",")]
    if "*" in candidatos or vigente in candidatos:
        return
    raise ApiError(412, "VERSION_OBSOLETA", "El recurso cambió; vuelva a consultarlo")


# ---------------------------------------------------------------- paginación
def paginacion(page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100)) -> tuple[int, int]:
    return page, pageSize


def pagina(db, sql_from: str, params: list, select: str, order: str, pg: tuple[int, int], mapper):
    page, size = pg
    total = db.execute(f"SELECT count(*) {sql_from}", params).fetchone()[0]
    filas = db.execute(f"SELECT {select} {sql_from} ORDER BY {order} LIMIT ? OFFSET ?",
                       params + [size, (page - 1) * size]).fetchall()
    return {"items": [mapper(f) for f in filas], "pagination": {"page": page, "pageSize": size, "total": total}}


def es_administrador(db, usuario_id: str) -> bool:
    return db.execute("SELECT 1 FROM usuario_administracion WHERE usuario_id=? AND perfil_administracion='Administrador'",
                      (usuario_id,)).fetchone() is not None
