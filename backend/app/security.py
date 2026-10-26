"""Autenticación y autorización (S05-S06-A2).

- Contraseñas: bcrypt (sal aleatoria por contraseña).
- Token: JWT HS256 firmado con JWT_SECRET (variable de entorno) y con expiración `exp` = JWT_EXPIRATION minutos.
- `usuario_actual`: valida `Authorization: Bearer <token>`; sin token, firma inválida, token vencido, usuario
  inexistente o cuenta no activa -> 401.
- `autorizar`: se aplica a todos los routers CRUD (main.py). Exige un token válido y que el rol del usuario
  esté en `PERMISOS` para la ruta (x-roles del openapi_equipo.yaml); si no -> 403. Una ruta que no esté en la
  tabla se rechaza (falla cerrada).
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import config
from .db import get_db
from .util import ApiError, prohibido

# ---------------------------------------------------------------- contraseñas
BCRYPT_MAX_BYTES = 72  # bcrypt solo usa los primeros 72 bytes; se rechazan contraseñas más largas


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, TypeError):  # hash con formato inválido o contraseña > 72 bytes
        return False


# Hash de relleno: si el correo no existe se verifica contra él, para que la respuesta tarde lo mismo
# y no revele qué correos están registrados.
HASH_RELLENO = hash_password("contraseña-de-relleno")


# ---------------------------------------------------------------- tokens
def crear_token(usuario) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario["id"],
        "rol": usuario["rol"],
        "iat": ahora,
        "exp": ahora + timedelta(minutes=config.JWT_EXPIRATION),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def no_autenticado() -> ApiError:
    return ApiError(401, "NO_AUTENTICADO", "Inicie sesión para continuar")


_bearer = HTTPBearer(auto_error=False)  # auto_error=False: respondemos nosotros con 401 y el esquema Error


def usuario_actual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer), db=Depends(get_db)):
    """Usuario autenticado a partir del JWT. Reemplaza al encabezado X-Actor-Id de la entrega anterior."""
    if cred is None or cred.scheme.lower() != "bearer":
        raise no_autenticado()
    try:
        payload = jwt.decode(cred.credentials, config.JWT_SECRET,
                             algorithms=[config.JWT_ALGORITHM],          # fijo: evita alg=none / confusión de algoritmo
                             options={"require": ["exp", "iat", "sub"]})
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "SESION_EXPIRADA", "La sesión expiró; inicie sesión de nuevo")
    except jwt.InvalidTokenError:  # firma inválida, token mal formado, claims faltantes
        raise no_autenticado()
    fila = db.execute("SELECT * FROM usuario WHERE id = ?", (payload["sub"],)).fetchone()
    if not fila or fila["estado_cuenta"] != "Activa":
        raise no_autenticado()
    return fila


# Quién ejecuta la acción: mismo nombre que usaban los routers (antes salía de X-Actor-Id).
actor = usuario_actual

# ---------------------------------------------------------------- autorización por rol
# Generada de `x-roles` de openapi_equipo.yaml (todas estas operaciones tienen security: bearerAuth).
# Clave: (método, ruta sin API_PREFIX). Conjunto vacío = ningún rol (x-roles: [ninguno]).
RES, VIG, MANT, ADMIN = "Residente", "Vigilancia", "Mantenimiento", "Administracion"
TODOS = frozenset({RES, VIG, MANT, ADMIN})
PERMISOS: dict[tuple[str, str], frozenset[str]] = {
    # Catálogo
    ("GET", "/units"): frozenset({ADMIN, VIG}),
    ("POST", "/units"): frozenset({ADMIN}),
    ("GET", "/units/{unitId}"): frozenset({ADMIN, VIG}),
    ("PATCH", "/units/{unitId}"): frozenset({ADMIN}),
    ("GET", "/common-areas"): TODOS,
    ("POST", "/common-areas"): frozenset({ADMIN}),
    ("GET", "/common-areas/{areaId}"): TODOS,
    ("PATCH", "/common-areas/{areaId}"): frozenset({ADMIN}),
    ("GET", "/categories"): frozenset({RES, VIG, ADMIN}),
    ("GET", "/parameters"): frozenset({ADMIN}),
    ("PUT", "/parameters/{clave}"): frozenset({ADMIN}),
    ("GET", "/parameters/{clave}/changes"): frozenset({ADMIN}),
    # Usuarios y responsables
    ("GET", "/users"): frozenset({ADMIN}),
    ("POST", "/users"): frozenset({ADMIN}),
    ("GET", "/users/{userId}"): frozenset({ADMIN}),
    ("PATCH", "/users/{userId}"): frozenset({ADMIN}),
    ("GET", "/users/{userId}/unit-links"): frozenset({ADMIN}),
    ("POST", "/users/{userId}/unit-links"): frozenset({ADMIN}),
    ("GET", "/assignees"): frozenset({ADMIN}),
    ("GET", "/external-providers"): frozenset({ADMIN}),
    ("POST", "/external-providers"): frozenset({ADMIN}),
    ("GET", "/external-providers/{providerId}"): frozenset({ADMIN}),
    ("PATCH", "/external-providers/{providerId}"): frozenset({ADMIN}),
    ("GET", "/delegations"): frozenset({ADMIN}),
    ("POST", "/delegations"): frozenset({ADMIN}),
    ("PATCH", "/delegations/{delegationId}"): frozenset({ADMIN}),
    # Reportes
    ("GET", "/reports"): TODOS,
    ("POST", "/reports"): frozenset({RES, VIG, ADMIN}),
    ("GET", "/reports/possible-duplicates"): frozenset({ADMIN}),
    ("GET", "/reports/{folio}"): TODOS,
    ("PATCH", "/reports/{folio}"): frozenset({RES, ADMIN}),
    ("DELETE", "/reports/{folio}"): frozenset(),  # nada se borra (RNF-07)
    ("GET", "/reports/{folio}/history"): frozenset({RES, MANT, ADMIN}),
    ("GET", "/reports/{folio}/notes"): frozenset({MANT, ADMIN}),
    ("POST", "/reports/{folio}/notes"): frozenset({MANT, ADMIN}),
    ("PUT", "/reports/{folio}/visit"): frozenset({MANT, ADMIN}),
    ("DELETE", "/reports/{folio}/visit"): frozenset({MANT, ADMIN}),
    ("POST", "/reports/{folio}/holds"): frozenset({MANT, ADMIN}),
    ("PATCH", "/reports/{folio}/holds/{holdId}"): frozenset({MANT, ADMIN}),
    ("GET", "/reports/{folio}/costs"): frozenset({ADMIN}),
    ("POST", "/reports/{folio}/costs"): frozenset({ADMIN}),
    ("GET", "/reports/{folio}/persistence-indications"): frozenset({ADMIN}),
    ("POST", "/reports/{folio}/persistence-indications"): frozenset({RES}),
    # Avisos
    ("GET", "/notifications"): TODOS,
    ("PATCH", "/notifications/{notificationId}"): TODOS,
    ("GET", "/email-deliveries"): frozenset({ADMIN}),
}


def autorizar(request: Request, usuario=Depends(usuario_actual)):
    """Dependencia de los routers protegidos: 401 sin token válido (usuario_actual), 403 si el rol no está
    autorizado para la operación."""
    ruta = request.scope["route"].path.removeprefix(config.API_PREFIX)
    roles = PERMISOS.get((request.method, ruta))
    if roles is None or usuario["rol"] not in roles:
        raise prohibido()
    return usuario
