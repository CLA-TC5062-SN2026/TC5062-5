"""ReportaYa API — FastAPI con autenticación JWT, control de acceso por rol y por registro, flujo de estados,
avisos y tablero (S11-A1)."""

import asyncio
import logging
import sqlite3
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config
from .db import connect
from .idempotencia import middleware_idempotencia
from .notificaciones import ciclo_de_mantenimiento
from .routers import archivos, auth, avisos, catalogo, flujo, metricas, reportes, usuarios
from .security import autorizar
from .util import ApiError

log = logging.getLogger("reportaya")


def _una_vuelta():
    conn = connect()
    try:
        ciclo_de_mantenimiento(conn)
    except Exception:  # una falla de la tarea nunca tumba el servidor
        log.exception("Falla en la tarea periódica")
    finally:
        conn.close()


async def _tareas_periodicas():
    """Cada CORREO_REVISION_SEGUNDOS: reintentos de correo (RF-11) y alertas de estancamiento (RF-22).

    Corre en un hilo aparte: en la prueba de carga (RNF-03), la primera vuelta sobre 5,000 reportes generó
    las alertas pendientes en ~10 s y, dentro del bucle de eventos, detenía todas las peticiones mientras tanto."""
    while True:
        await asyncio.sleep(config.CORREO_REVISION_SEGUNDOS)
        await asyncio.to_thread(_una_vuelta)


@asynccontextmanager
async def _ciclo_de_vida(_: FastAPI):
    tarea = asyncio.create_task(_tareas_periodicas())
    yield
    tarea.cancel()


app = FastAPI(
    title="ReportaYa API",
    version="1.1.0",
    docs_url="/docs",
    openapi_url=f"{config.API_PREFIX}/openapi.json",
    lifespan=_ciclo_de_vida,
)
# Públicos: /auth/login, /account-activations, /password-reset-requests y /password-resets.
# Protegidos: /auth/me (usuario_actual) y TODOS los demás routers (autorizar = JWT válido + rol permitido según
# x-roles de openapi_equipo.yaml). La visibilidad por registro (matriz 2.3) la aplica cada endpoint.
app.include_router(auth.router, prefix=config.API_PREFIX)
app.include_router(auth.cuentas_router, prefix=config.API_PREFIX)
for r in (
    catalogo.router,
    usuarios.router,
    reportes.router,
    flujo.router,
    archivos.router,
    metricas.router,
    avisos.router,
):
    app.include_router(r, prefix=config.API_PREFIX, dependencies=[Depends(autorizar)])


app.middleware("http")(middleware_idempotencia)  # RNF-11: reintentos seguros de la PWA


@app.middleware("http")
async def _renovar_sesion(request: Request, call_next):
    """RNF-06: devuelve el token renovado de la petición autenticada (ver security.usuario_actual)."""
    respuesta = await call_next(request)
    nuevo = getattr(request.state, "token_renovado", None)
    if nuevo and respuesta.status_code < 400:
        respuesta.headers["X-Token-Renovado"] = nuevo
    return respuesta


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
    if all(
        x["loc"][0] == "path" for x in errs
    ):  # un identificador mal formado no puede existir: 404 (el YAML no declara 400 en estos GET)
        return _error(404, "NO_ENCONTRADO", "Recurso no encontrado")
    if any(x["loc"][0] == "body" and x["type"] == "missing" for x in errs) and not any(
        x["loc"][0] != "body" for x in errs
    ):
        return _error(
            422,
            "VALIDACION",
            "Datos inválidos",
            [{"campo": ".".join(map(str, x["loc"][1:])) or "cuerpo", "mensaje": "Campo obligatorio"} for x in errs],
        )
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
    conn = connect()
    try:
        tablas = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    finally:
        conn.close()
    return {"estado": "ok", "baseDeDatos": str(config.DATABASE_PATH.name), "tablas": tablas, "llavesForaneas": bool(fk)}


# ------------------------------------------------------------------ SPA en el mismo proceso (despliegue en Render)
# Con Docker Compose la sirve Caddy; en un solo contenedor (Render) la sirve el API si FRONTEND_DIST existe.
if config.FRONTEND_DIST and (config.FRONTEND_DIST / "index.html").exists():
    from fastapi.responses import FileResponse

    _DIST = config.FRONTEND_DIST.resolve()
    _SIN_CACHE = {"Cache-Control": "no-cache"}  # index y service worker: siempre la versión publicada

    @app.middleware("http")
    async def encabezados_de_seguridad(request: Request, call_next):
        respuesta = await call_next(request)
        respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
        respuesta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.headers.get("x-forwarded-proto") == "https":
            respuesta.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return respuesta

    @app.get("/{ruta:path}", include_in_schema=False)
    def spa(ruta: str):
        if ruta.startswith(config.API_PREFIX.strip("/") + "/"):
            return _error(404, "NO_ENCONTRADO", "Recurso no encontrado")
        archivo = (_DIST / ruta).resolve()
        if ruta and archivo.is_file() and archivo.is_relative_to(_DIST):
            inmutable = ruta.startswith("assets/")  # nombres con hash de Vite
            cabeceras = {"Cache-Control": "public, max-age=31536000, immutable"} if inmutable else _SIN_CACHE
            return FileResponse(archivo, headers=cabeceras)
        return FileResponse(_DIST / "index.html", headers=_SIN_CACHE)  # rutas de React Router


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT)
