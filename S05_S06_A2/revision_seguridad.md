# Revisión de seguridad del API — S05-S06-A2

Backend: `backend/` (Python · FastAPI · SQLite) · librerías: `bcrypt` (hash de contraseñas) y `PyJWT` (tokens).
Archivos del módulo: `app/security.py` (hash, JWT, middleware y tabla de permisos), `app/routers/auth.py`
(`/auth/register`, `/auth/login`, `/auth/me`), `app/config.py` (variables de entorno), `app/main.py` (dónde se aplica).
Todas las rutas llevan el prefijo `API_PREFIX=/api/v1` (p. ej. `POST /api/v1/auth/login`).

## 1. Checklist de la actividad

| # | Pregunta | Resultado | Evidencia en el código |
|---|---|---|---|
| 1 | ¿El JWT tiene expiración explícita? | **Sí.** Cada token lleva `exp` = emisión + `JWT_EXPIRATION` minutos (30 por defecto, RNF-06). Además el decodificador **exige** que existan `exp`, `iat` y `sub`: un token sin `exp` se rechaza. | `app/security.py` L50-51: `"iat": ahora,` / `"exp": ahora + timedelta(minutes=config.JWT_EXPIRATION)` · L70: `options={"require": ["exp", "iat", "sub"]}` · `app/config.py` L33: `JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "30"))` |
| 2 | ¿`/register` devuelve la contraseña? | **No.** La respuesta se arma con `user_out`, que solo copia `id, nombre, correo, rol, estadoCuenta` (+ vinculación); nunca `contrasena_hash`. La contraseña solo se guarda como hash bcrypt. | `app/routers/auth.py` L64: `... VALUES (?,?,?, 'Residente', 'Activa', ?)""", (..., hash_password(d.password))` · L69: `return responder(user_out(db, u), 201, ...)` · `app/serial.py` L40-41 (campos de `user_out`) · `app/security.py` L27: `bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())` |
| 3 | ¿El middleware rechaza firma inválida o token expirado? | **Sí, con 401.** El algoritmo está fijo (`HS256`), así que un token `alg=none` o firmado con otra clave también se rechaza. Un usuario borrado/desactivado después de emitir el token también recibe 401. | `app/security.py` L68-75: `jwt.decode(..., algorithms=[config.JWT_ALGORITHM], ...)` · `except jwt.ExpiredSignatureError:` → 401 `SESION_EXPIRADA` · `except jwt.InvalidTokenError:` → 401 `NO_AUTENTICADO` · L76: `if not fila or fila["estado_cuenta"] != "Activa":` → 401 |
| 4 | ¿El secret está en código duro o en variable de entorno? | **Variable de entorno.** `.env` está en `.gitignore`; `.env.example` solo trae un marcador. Si `JWT_SECRET` falta, mide menos de 32 caracteres o es el marcador del ejemplo, **la aplicación no arranca**. | `app/config.py` L29-31: `JWT_SECRET = os.getenv("JWT_SECRET", "")` / `if len(JWT_SECRET) < 32 or JWT_SECRET.startswith("cambie-este-valor"): raise RuntimeError(...)` · `backend/.env.example`: `JWT_SECRET=...` y `JWT_EXPIRATION=30` |

Las pruebas 1, 10, 11, 12 y 13 de la sección 3.2 son la verificación de estos cuatro puntos con el servidor en marcha.

## 2. Hallazgos y correcciones

| # | Hallazgo | Origen | Corrección |
|---|---|---|---|
| C-1 | **Suplantación con `X-Actor-Id`.** En la entrega anterior quien ejecutaba la acción salía del encabezado `X-Actor-Id` y, si faltaba, se usaba el primer Administrador: cualquiera podía actuar como cualquier usuario, o como Administrador sin enviar nada. | Código de S05-S06-A1 (`app/util.py` L134-147, función `actor`) | Se eliminó `actor` de `util.py`. Ahora `actor = usuario_actual` (`app/security.py`): el usuario sale **solo** del JWT. Prueba 19: enviar `X-Actor-Id` sin token → 401. |
| C-2 | **Un registro público podía crear administradores.** La actividad pide `POST /auth/register` público; si el cuerpo aceptara `rol`, cualquiera se registraría como `Administracion`. | Revisión del diseño del registro contra el modelo de roles | El esquema `Registro` no tiene `rol` y hereda `extra="forbid"` (`app/schemas.py` L22 y L244): un campo `rol` responde 400. El INSERT fija `'Residente'` (`auth.py` L64) y exige una unidad existente. Prueba 2. |
| C-3 | **Usuarios demo sin contraseña real.** `init_db.py --demo` guardaba `contrasena_hash = 'hash-demo'`: nadie podía iniciar sesión y no se podía probar el 403 con otros roles. | Código de S05-S06-A1 (`scripts/init_db.py`) | Hash bcrypt real de `Demo1234!` para los 5 usuarios demo (`init_db.py` L64 y L76-77). Solo para datos locales de ejemplo. |
| C-4 | **Secreto de ejemplo utilizable.** Si alguien copia `.env.example` tal cual, el secreto sería público (está en GitHub) y cualquiera podría firmar tokens. | Revisión de `.env.example` | `config.py` L30 rechaza el marcador `cambie-este-valor...` y secretos de menos de 32 caracteres. |
| C-5 | **Precedencia 403 vs 404.** La prueba de contrato encontró que `DELETE /reports/RY-999999` ahora responde 403 y no 404, porque el rol se valida antes de buscar el recurso. | Prueba `tests/test_contrato.py` (759 verificaciones, 1 fallo) | Se mantiene a propósito: un rol sin permiso no debe poder averiguar qué folios existen (OWASP: no revelar existencia). Se ajustó la prueba (L370) y se documenta aquí como divergencia con el orden 404→403 del contrato. Resultado final: 759 verificaciones, 0 fallos. |
| C-6 | **Enumeración de correos.** Un mensaje distinto para «correo no existe» y «contraseña incorrecta» revelaría qué correos están registrados. | Revisión de `/auth/login` contra RF-01-AC-2 | Mismo 401 `CREDENCIALES_INVALIDAS` en todos los casos (`auth.py` `_credenciales_invalidas`) y, si el correo no existe, se verifica contra un hash de relleno para que el tiempo de respuesta sea similar (`auth.py` L77, `security.py` L41). Pruebas 5 y 6. |
| C-7 | **Fuerza bruta.** Sin límite de intentos se podría probar contraseñas sin fin. | RNF-06 del SRS (5 intentos → 15 min) | `auth.py` L17-18 y L84-85: al 5.º intento fallido se fija `bloqueado_hasta` (+15 min); durante el bloqueo incluso la contraseña correcta recibe el mismo 401. Prueba 20. |
| C-8 | **Límite de bcrypt.** bcrypt solo usa los primeros 72 bytes y la versión 5 lanza error con contraseñas más largas (sería un 500). | Revisión de la librería | `auth.py` `_validar_password`: 8 caracteres mínimo, 72 bytes máximo → 422. |

## 3. Protección de rutas

### 3.1 Cómo se aplica

- `app/main.py` L22: los 4 routers CRUD se registran con `dependencies=[Depends(autorizar)]`, así que **las 46 operaciones CRUD** pasan por el middleware. En el `openapi_equipo.yaml` las 46 heredan `security: bearerAuth` (ninguna tiene `security: []`).
- `autorizar` (`app/security.py` L143-149): 1) `usuario_actual` valida el token (401); 2) busca `(método, ruta)` en la tabla `PERMISOS`, copiada de `x-roles` del YAML; si el rol no está → 403. **Falla cerrada:** una ruta nueva que no se agregue a la tabla responde 403 a todos.
- Rutas públicas (`security: []`): `POST /auth/register`, `POST /auth/login`. `GET /auth/me` exige token (cualquier rol). `GET /health` (diagnóstico, fuera del YAML) sigue público.

| Nivel de acceso | Operaciones |
|---|---|
| Cualquier rol autenticado (Residente, Vigilancia, Mantenimiento, Administración) | `GET /common-areas`, `GET /common-areas/{areaId}`, `GET /reports`, `GET /reports/{folio}`, `GET /notifications`, `PATCH /notifications/{notificationId}`, `GET /auth/me` |
| Residente, Vigilancia, Administración | `GET /categories`, `POST /reports` |
| Administración, Vigilancia | `GET /units`, `GET /units/{unitId}` |
| Residente, Mantenimiento, Administración | `GET /reports/{folio}/history` |
| Residente, Administración | `PATCH /reports/{folio}` |
| Mantenimiento, Administración | `GET`/`POST /reports/{folio}/notes`, `PUT`/`DELETE /reports/{folio}/visit`, `POST /reports/{folio}/holds`, `PATCH /reports/{folio}/holds/{holdId}` |
| Solo Residente | `POST /reports/{folio}/persistence-indications` |
| Solo Administración | `POST /units`, `PATCH /units/{unitId}`, `POST /common-areas`, `PATCH /common-areas/{areaId}`, `GET /parameters`, `PUT /parameters/{clave}`, `GET /parameters/{clave}/changes`, `GET`/`POST /users`, `GET`/`PATCH /users/{userId}`, `GET`/`POST /users/{userId}/unit-links`, `GET /assignees`, `GET`/`POST /external-providers`, `GET`/`PATCH /external-providers/{providerId}`, `GET`/`POST /delegations`, `PATCH /delegations/{delegationId}`, `GET /reports/possible-duplicates`, `GET`/`POST /reports/{folio}/costs`, `GET /reports/{folio}/persistence-indications`, `GET /email-deliveries` |
| Ningún rol (`x-roles: [ninguno]`, RNF-07: nada se borra) | `DELETE /reports/{folio}` → siempre 403 |

Dentro de una ruta permitida siguen las reglas que ya existían: solo el perfil **Administrador** (no la Auxiliar) modifica parámetros y delegaciones (403), y un Residente no puede enviar campos de captura al crear un reporte (403).

### 3.2 Pruebas manuales (curl)

Ejecutadas el 25-oct-2026 con el servidor en `http://127.0.0.1:8000` y la BD recién creada (`python scripts/init_db.py --reset --demo`). Comandos curl (la petición de cada caso está en la tabla); el flujo del video usa la colección de Postman `S05_S06_A2/pruebas_auth.json`. Usuarios demo `*@reportaya.demo`, contraseña `Demo1234!`. Los tokens se abrevian como `<token>`.

| # | Caso | Petición | Esperado | Obtenido |
|---|---|---|---|---|
| 1 | Registro válido | `POST /auth/register` (nombre, correo, password, unidadId de B-502, ocupacion) | 201 sin contraseña | **201** `{"id":"8a6e…","rol":"Residente","estadoCuenta":"Activa","vinculacion":{…}}` — sin `password` ni hash |
| 2 | Registro eligiendo rol | mismo cuerpo + `"rol":"Administracion"` | 400 | **400** `PETICION_INVALIDA: … campo desconocido: rol` |
| 3 | Correo repetido | `POST /auth/register` con el mismo correo | 422 | **422** `Ya existe un usuario con ese correo` |
| 4 | Login correcto | `POST /auth/login` | 200 + token | **200** `{"token":"eyJhbGciOiJIUzI1NiIs…","tipo":"Bearer","expiraEn":1800,"usuario":{…}}` |
| 5 | Contraseña incorrecta | `POST /auth/login` | 401 | **401** `CREDENCIALES_INVALIDAS` |
| 6 | Correo inexistente | `POST /auth/login` | 401 (mismo mensaje) | **401** `CREDENCIALES_INVALIDAS` |
| 7 | `me` con token | `GET /auth/me` + `Authorization: Bearer <token de residente>` | 200 | **200** `{"nombre":"Rosa Residente","rol":"Residente","unidad":{"etiqueta":"B-502",…}}` |
| 8 | `me` sin token | `GET /auth/me` | 401 | **401** `NO_AUTENTICADO` |
| 9 | **Ruta protegida sin token** | `GET /users` | 401 | **401** `NO_AUTENTICADO` |
| 10 | **Token inválido** (último carácter cambiado) | `GET /users` + token alterado | 401 | **401** `NO_AUTENTICADO` |
| 11 | Token vencido (`exp` en el pasado, firmado con el secreto correcto) | `GET /users` | 401 | **401** `SESION_EXPIRADA` |
| 12 | Token firmado con otro secreto | `GET /users` | 401 | **401** `NO_AUTENTICADO` |
| 13 | Token `alg=none` (sin firma) | `GET /users` | 401 | **401** `NO_AUTENTICADO` |
| 14 | **Rol incorrecto** | `GET /users` con token de Residente | 403 | **403** `PROHIBIDO` |
| 15 | **Rol incorrecto** | `POST /units` con token de Residente | 403 | **403** `PROHIBIDO` |
| 16 | **Token válido y rol correcto** | `GET /users` con token de Administración | 200 | **200** `{"items":[…],"pagination":{…,"total":6}}` |
| 17 | **Token válido y rol correcto** | `POST /units` con token de Administración | 201 | **201** `{"etiqueta":"C-301",…}` |
| 18 | **Token válido y rol correcto** | `GET /units` con token de Vigilancia | 200 | **200** `{"items":[…],"pagination":{…,"total":2}}` |
| 19 | Encabezado anterior | `GET /users` + `X-Actor-Id: <id del Administrador>` sin token | 401 | **401** `NO_AUTENTICADO` |
| 20 | Bloqueo | 5 logins fallidos y luego la contraseña correcta | 401 ×6 | **401** ×5 y **401** con la contraseña correcta |

Además, `tests/test_contrato.py` (actualizado para iniciar sesión y usar el token de cada rol) ejercita 49 operaciones del YAML con **759 verificaciones y 0 fallos**.

## 4. Pendientes conocidos

- **Expiración por inactividad.** El YAML dice «30 min de inactividad»; se implementó vigencia fija de 30 min (`exp`). Renovar el token con cada petición requiere un endpoint de refresco.
- **Cierre de sesión.** Un JWT no se puede revocar antes de su `exp` sin guardar sesiones en el servidor; `DELETE /sessions/current` sigue sin implementarse.
- **Matriz de visibilidad (RNF-05, RD-07).** El control actual es por operación. Falta filtrar *qué datos* ve cada rol (p. ej. Vigilancia no debería recibir el propietario en `GET /units`, y un Residente solo sus reportes).
- **Auto-registro vs EX-08.** El SRS dice que nadie se registra por su cuenta; `/auth/register` existe porque lo pide la actividad y se limitó al rol de menor privilegio (C-2). Documentado en `openapi_equipo.yaml`.
- `/sessions` y `/sessions/current` del contrato equivalen a `/auth/login` y `/auth/me`; se dejaron documentados ambos.
