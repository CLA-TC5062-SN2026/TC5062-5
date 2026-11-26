# ReportaYa API (backend)

FastAPI · SQLite (`db/esquema_bd.sql`) · JWT (PyJWT) + bcrypt · control de acceso por rol **y por registro** (matriz 2.3 del SRS).
La instalación completa, las variables de entorno y las pruebas están en el [README de la raíz](../README.md).

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # y ponga un JWT_SECRET propio
python scripts/cargar_demo.py                          # datos de demostración (contraseña Demo1234!)
uvicorn app.main:app --port 8000                       # documentación interactiva en /docs
python -m pytest tests/test_reglas.py -q               # reglas de negocio (122 casos)
```

## Estructura

```
app/main.py             aplicación, manejo de errores (esquema Error), /health, tarea periódica, token renovado
app/security.py         bcrypt, JWT, usuario_actual, autorizar y tabla de permisos por rol (x-roles del YAML)
app/visibilidad.py      matriz de visibilidad 2.3: qué reportes, campos, archivos e historial ve cada rol (RNF-05)
app/reglas.py           transiciones permitidas (RF-07), historial, parámetros (RF-27), gestión y delegación (RF-21)
app/notificaciones.py   avisos de RF-11 (sistema y correo), reintentos y reportes estancados (RF-22)
app/correo.py           interfaz ServicioCorreo y CorreoSimulado (archivos .txt en CORREO_BANDEJA_DIR)
app/cuentas.py          enlaces de activación y recuperación de un solo uso (RF-14), solo se guarda su hash
app/reloj.py            hora del sistema que las pruebas pueden fijar (RNF-10)
app/util.py schemas.py serial.py config.py db.py   errores, validación, serialización, configuración y conexión
app/routers/            auth (login, me, activación, recuperación) · catalogo · usuarios · reportes (alta, consulta,
                        corrección, notas, visita, detenciones, costos, persistencia) · flujo (asignación,
                        reclasificación, ciclos, terminado, confirmación, cierre, cancelación, reapertura,
                        duplicados, garantía) · archivos · metricas (tablero y PDF) · avisos
scripts/init_db.py      crea la base y el catálogo RD-01; --demo (datos de la prueba de contrato); --admin-correo
                        (comando de arranque del primer Administrador, RF-14-AC-4)
scripts/cargar_demo.py  condominio de demostración creado con el flujo real del API
tests/                  test_reglas.py + conftest.py (pytest, en proceso) · test_contrato.py (contra el servidor)
openapi_equipo.yaml     contrato vivo v1.1.0 (cambios respecto a la 1.0.0 en info.description)
```

Alcance: las 68 operaciones del contrato v1.1.0. Ya no existe `POST /auth/register`: toda cuenta la crea la
Administración (RF-02, EX-08).
