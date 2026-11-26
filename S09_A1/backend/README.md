# ReportaYa API — servicios CRUD con autenticación JWT

Python 3.11+ · FastAPI · SQLite (`db/esquema_bd.sql`) · JWT (PyJWT) + bcrypt · control de acceso por rol.

## Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # Windows: copy .env.example .env
#   y en .env ponga un JWT_SECRET propio: python -c "import secrets; print(secrets.token_urlsafe(48))"
python scripts/init_db.py --reset --demo               # crea reportaya.db, catálogo RD-01 y datos de ejemplo
python -m app.main                                     # o: uvicorn app.main:app --port 8000
```

- Verificar conexión a la BD: `GET http://127.0.0.1:8000/health` → `{"estado":"ok","tablas":33,"llavesForaneas":true}`
  (33 = las 32 tablas del esquema + `sqlite_sequence` que crea SQLite por el AUTOINCREMENT).
- Documentación interactiva: `http://127.0.0.1:8000/docs`.
- Pruebas de contrato (con el servidor corriendo y una BD recién creada con `--reset --demo`):
  `python tests/test_contrato.py`

## Autenticación (S05-S06-A2)

- `POST /api/v1/auth/register` (público, crea un Residente) · `POST /api/v1/auth/login` (público, devuelve el JWT) ·
  `GET /api/v1/auth/me` (con token).
- Todas las rutas CRUD exigen `Authorization: Bearer <token>` (401 sin token o con token inválido/vencido) y un rol
  autorizado según `x-roles` del `openapi_equipo.yaml` (403). Tabla de permisos: `app/security.py`.
- `init_db.py --demo` crea un usuario por rol (`admin`, `auxiliar`, `vigilancia`, `mantenimiento`, `residente`
  `@reportaya.demo`) con contraseña `Demo1234!`.
- Revisión de seguridad y pruebas: `../S05_S06_A2/revision_seguridad.md`.

## Estructura

```
app/main.py            aplicación, manejo de errores (esquema Error), /health, dónde se aplica la seguridad
app/security.py        bcrypt, JWT, middleware (usuario_actual, autorizar) y tabla de permisos por rol
app/config.py db.py    variables de entorno (.env) y conexión SQLite (PRAGMA foreign_keys=ON)
app/util.py            errores, fechas (BD en UTC, API en la zona del condominio), ETag/If-Match, paginación
app/schemas.py         validación de cuerpos (derivada de los schemas del YAML)
app/serial.py          filas -> JSON con los nombres de campo del YAML
app/routers/           auth (register, login, me) · catalogo (unidades, áreas, categorías, parámetros) · usuarios (usuarios, vinculaciones,
                       responsables, proveedores, delegaciones) · reportes · avisos
scripts/init_db.py     crea la BD y carga el catálogo
tests/test_contrato.py compara rutas/códigos/schemas contra openapi_equipo.yaml
```

## Alcance

46 de las 69 operaciones del YAML (todo el CRUD de las entidades principales). Quedan fuera, por pertenecer a
seguridad o a las reglas de negocio de la siguiente actividad: sesiones, activaciones y recuperación de contraseña;
transiciones de estado (`assignments`, `classification`, `cycles`, `completions`, `resident-responses`, `closures`,
`reopenings`, `cancellations`, `merges`, `duplicate-flag`); archivos descargables y compartidos; `warranty`; `metrics`.
Detalle y divergencias conocidas: sección «Correcciones al código generado» de `revision_sql.md`.
