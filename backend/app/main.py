"""ReportaYa API — servicios CRUD (Parte 2). Sin seguridad: JWT y roles son la siguiente actividad."""
import logging
import sqlite3

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config
from .routers import avisos, catalogo, reportes, usuarios
from .util import ApiError

log = logging.getLogger("reportaya")

app = FastAPI(title="ReportaYa API", version="1.0.0", docs_url="/docs", openapi_url=f"{config.API_PREFIX}/openapi.json")
for r in (catalogo.router, usuarios.router, reportes.router, avisos.router):
    app.include_router(r, prefix=config.API_PREFIX)


def _error(status: int, codigo: str, mensaje: str, errores=None) -> JSONResponse:
    cuerpo = {"codigo": codigo, "mensaje": mensaje}
    if errores:
        cuerpo["errores"] = errores
    return JSONResponse(cuerpo, status_code=status)


@app.exception_handler(ApiError)
async def _api_error(_: Request, e: ApiError):
    return _error(e.status, e.codigo, e.mensaje, e.errores)


@app.exception_handler(RequestValidationError)
async def _validacion_fastapi(_: Request, e: RequestValidationError):
    """Identificador de ruta mal formado -> 404; consulta/encabezado/JSON mal formado -> 400 (contrato: «no se pudo
    interpretar»); campos obligatorios ausentes en un formulario -> 422."""
    errs = e.errors()
    if all(x["loc"][0] == "path" for x in errs):  # un identificador mal formado no puede existir: 404 (el YAML no declara 400 en estos GET)
        return _error(404, "NO_ENCONTRADO", "Recurso no encontrado")
    if any(x["loc"][0] == "body" and x["type"] == "missing" for x in errs) and not any(x["loc"][0] != "body" for x in errs):
        return _error(422, "VALIDACION", "Datos inválidos",
                      [{"campo": ".".join(map(str, x["loc"][1:])) or "cuerpo", "mensaje": "Campo obligatorio"} for x in errs])
    detalle = [{"campo": ".".join(map(str, x["loc"])), "mensaje": x["msg"]} for x in errs]
    return _error(400, "PETICION_INVALIDA", "La petición no es válida", detalle)


@app.exception_handler(StarletteHTTPException)
async def _http(_: Request, e: StarletteHTTPException):
    if e.status_code == 404:
        return _error(404, "NO_ENCONTRADO", "Recurso no encontrado")
    if e.status_code == 405:
        return _error(405, "METODO_NO_PERMITIDO", "Método no permitido")
    return _error(e.status_code, "PETICION_INVALIDA", str(e.detail))


@app.exception_handler(sqlite3.IntegrityError)
async def _integridad(_: Request, e: sqlite3.IntegrityError):
    """Red de seguridad: la BD rechazó algo que la capa de validación no previó (ya se hizo ROLLBACK)."""
    log.warning("Restricción de BD: %s", e)
    return _error(422, "VALIDACION", "Datos inválidos", [{"campo": "cuerpo", "mensaje": str(e)}])


@app.exception_handler(Exception)
async def _inesperado(_: Request, e: Exception):
    log.exception("Error inesperado")
    return _error(500, "ERROR_INTERNO", "Ocurrió un error inesperado")


@app.get("/health", include_in_schema=False)
def health():
    """Verifica que el servidor responde y que la conexión a la base de datos funciona."""
    from .db import connect
    conn = connect()
    try:
        tablas = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    finally:
        conn.close()
    return {"estado": "ok", "baseDeDatos": str(config.DATABASE_PATH.name), "tablas": tablas, "llavesForaneas": bool(fk)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT)
