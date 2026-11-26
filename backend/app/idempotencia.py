"""Idempotency-Key en los POST (RNF-11): la PWA reintenta los envíos que quedaron pendientes sin señal; si el
servidor ya había procesado la petición, devuelve la misma respuesta en lugar de crear un reporte duplicado.

Se guarda por (usuario, clave): la ruta, el código y el cuerpo de la primera respuesta exitosa (2xx). Una
respuesta de error no se guarda, para que el reintento pueda corregirse. Si llega un reintento mientras la
primera petición todavía está en curso, responde 409 «La petición ya está en proceso».
"""

import sqlite3

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse, Response

from . import config
from .db import connect
from .util import now_utc


def _usuario(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        return jwt.decode(auth[7:], config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])["sub"]
    except jwt.InvalidTokenError:
        return None  # la autenticación la rechaza después el endpoint (401)


def _ejecutar(sql: str, params: tuple):
    db = connect()
    try:
        return db.execute(sql, params).fetchone()
    finally:
        db.close()


def _respuesta_previa(previa, ruta: str) -> Response:
    """Reintento de una clave conocida: otra operación (422), aún en curso (409) o la respuesta original."""
    if previa["ruta"] != ruta:
        return JSONResponse(
            {
                "codigo": "VALIDACION",
                "mensaje": "La clave de idempotencia ya se usó en otra operación",
                "errores": [{"campo": "Idempotency-Key", "mensaje": "Ya se usó en otra operación"}],
            },
            422,
        )
    if previa["estado"] == "EnCurso":
        return JSONResponse({"codigo": "EN_PROCESO", "mensaje": "La petición ya está en proceso"}, 409)
    headers = {"Idempotent-Replayed": "true"}
    if previa["location"]:
        headers["Location"] = previa["location"]
    return Response(previa["cuerpo"], previa["status"], headers=headers, media_type="application/json")


def _clave_valida(request: Request):
    """(usuario, clave) si la petición es un POST autenticado con Idempotency-Key; si no, None."""
    clave = request.headers.get("idempotency-key")
    if request.method != "POST" or not clave or not 8 <= len(clave) <= 200:
        return None
    usuario = _usuario(request)
    return (usuario, clave) if usuario else None


async def middleware_idempotencia(request: Request, call_next):
    llave = _clave_valida(request)
    if not llave:
        return await call_next(request)
    usuario, clave = llave
    ruta = request.url.path
    previa = _ejecutar("SELECT * FROM idempotencia WHERE usuario_id=? AND clave=?", llave)
    if previa:
        return _respuesta_previa(previa, ruta)
    try:
        _ejecutar(
            "INSERT INTO idempotencia (usuario_id, clave, ruta, fecha) VALUES (?,?,?,?)", (*llave, ruta, now_utc())
        )
    except sqlite3.IntegrityError:  # otro reintento con la misma clave ganó la carrera entre la consulta y el alta
        return JSONResponse({"codigo": "EN_PROCESO", "mensaje": "La petición ya está en proceso"}, 409)
    borrar = ("DELETE FROM idempotencia WHERE usuario_id=? AND clave=?", llave)
    try:
        respuesta = await call_next(request)
        cuerpo = b"".join([parte async for parte in respuesta.body_iterator])
    except BaseException:
        _ejecutar(*borrar)  # un error inesperado no deja la clave bloqueada «en curso»
        raise
    if 200 <= respuesta.status_code < 300:
        _ejecutar(
            "UPDATE idempotencia SET estado='Hecha', status=?, cuerpo=?, location=? WHERE usuario_id=? AND clave=?",
            (respuesta.status_code, cuerpo.decode("utf-8"), respuesta.headers.get("location"), usuario, clave),
        )
    else:
        _ejecutar(*borrar)
    return Response(cuerpo, respuesta.status_code, headers=dict(respuesta.headers), media_type=respuesta.media_type)
