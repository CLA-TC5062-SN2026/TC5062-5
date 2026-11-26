#!/bin/sh
# Arranque en Render. El disco del plan gratuito se borra en cada reinicio, así que la base se prepara al iniciar:
#   DEMO_AL_INICIAR=1  -> carga el condominio de demostración (16 reportes, contraseña «Demo1234!»)
#   si no              -> esquema y catálogo; el primer Administrador con ADMIN_CORREO y ADMIN_NOMBRE
set -e
if [ "$DEMO_AL_INICIAR" = "1" ]; then
    python scripts/cargar_demo.py
elif [ -n "$ADMIN_CORREO" ]; then
    python scripts/init_db.py --admin-correo "$ADMIN_CORREO" --admin-nombre "${ADMIN_NOMBRE:-Administrador}"
else
    python scripts/init_db.py
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}" --proxy-headers --forwarded-allow-ips "*"
