#!/bin/sh
# Crea la base con el esquema y el catálogo RD-01 si todavía no existe (no borra datos) y arranca el API.
set -e
python scripts/init_db.py
exec "$@"
