"""Respaldo y restauración (RNF-14): copia diaria de la base y de las fotos, con rotación.

    python scripts/respaldo.py crear                 # un respaldo ahora (lo usa el servicio `respaldo` de Compose)
    python scripts/respaldo.py crear --cada 24       # se queda corriendo: uno al iniciar y luego cada 24 h
    python scripts/respaldo.py listar
    python scripts/respaldo.py restaurar RUTA         # con el API detenido: reemplaza base y fotos por las del respaldo

Cada respaldo es una carpeta `AAAAMMDD-HHMMSS/` en RESPALDO_DIR con:
  - reportaya.db: copia consistente hecha con la API de respaldo de SQLite (funciona con el servidor en marcha),
    verificada con `PRAGMA integrity_check` antes de darla por buena;
  - fotos.tar.gz: las fotos y videos del almacén local (con ALMACEN=s3 las fotos se respaldan con el versionado
    del bucket, que es más barato que copiarlas; ver README);
  - manifiesto.json: fecha, número de reportes y tamaños, para revisar el respaldo sin abrirlo.
Se conservan los RESPALDO_CONSERVAR más recientes (14 por omisión: dos semanas de respaldos diarios).
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config  # noqa: E402

DESTINO = Path(os.getenv("RESPALDO_DIR", str(config.BASE_DIR / "respaldos")))
CONSERVAR = int(os.getenv("RESPALDO_CONSERVAR", "14"))
NOMBRE = re.compile(r"\d{8}-\d{6}")  # carpeta de un respaldo completo


def crear(destino: Path = DESTINO, conservar: int = CONSERVAR) -> Path:
    carpeta = destino / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    temporal = carpeta.with_name(carpeta.name + ".incompleto")
    temporal.mkdir(parents=True)
    base = temporal / "reportaya.db"
    origen = sqlite3.connect(config.DATABASE_PATH)
    copia = sqlite3.connect(base)
    with copia:
        origen.backup(copia)  # copia en línea y consistente aunque el API esté escribiendo
    origen.close()
    estado = copia.execute("PRAGMA integrity_check").fetchone()[0]
    reportes = copia.execute("SELECT COUNT(*) FROM reporte").fetchone()[0]
    copia.close()
    if estado != "ok":
        shutil.rmtree(temporal)
        raise RuntimeError(f"La copia de la base no pasó la verificación de integridad: {estado}")
    fotos = 0
    if config.ALMACEN == "local" and config.UPLOAD_DIR.exists():
        with tarfile.open(temporal / "fotos.tar.gz", "w:gz") as tar:
            tar.add(config.UPLOAD_DIR, arcname="uploads")
        fotos = sum(1 for p in config.UPLOAD_DIR.rglob("*") if p.is_file())
    manifiesto = {
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reportes": reportes,
        "archivos": fotos,
        "almacen": config.ALMACEN,
        "bytes": {p.name: p.stat().st_size for p in temporal.iterdir()},
    }
    (temporal / "manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.rename(carpeta)  # solo un respaldo completo lleva el nombre definitivo
    for viejo in respaldos(destino)[conservar:]:
        shutil.rmtree(viejo)
    return carpeta


def respaldos(destino: Path = DESTINO) -> list:
    """Respaldos completos, del más reciente al más antiguo."""
    if not destino.exists():
        return []
    return sorted((p for p in destino.iterdir() if p.is_dir() and NOMBRE.fullmatch(p.name)), reverse=True)


def restaurar(carpeta: Path) -> None:
    base = carpeta / "reportaya.db"
    prueba = sqlite3.connect(base)
    estado = prueba.execute("PRAGMA integrity_check").fetchone()[0]
    prueba.close()
    if estado != "ok":
        raise RuntimeError(f"El respaldo está dañado: {estado}")
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    for sufijo in ("-wal", "-shm"):
        Path(str(config.DATABASE_PATH) + sufijo).unlink(missing_ok=True)
    shutil.copy2(base, config.DATABASE_PATH)
    fotos = carpeta / "fotos.tar.gz"
    if fotos.exists():
        shutil.rmtree(config.UPLOAD_DIR, ignore_errors=True)
        with tarfile.open(fotos) as tar:
            tar.extractall(config.UPLOAD_DIR.parent / "_restaurando", filter="data")
        (config.UPLOAD_DIR.parent / "_restaurando" / "uploads").rename(config.UPLOAD_DIR)
        (config.UPLOAD_DIR.parent / "_restaurando").rmdir()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="accion", required=True)
    c = sub.add_parser("crear")
    c.add_argument("--cada", type=float, help="horas entre respaldos; sin esta opción hace uno y termina")
    sub.add_parser("listar")
    r = sub.add_parser("restaurar")
    r.add_argument("carpeta", type=Path)
    a = ap.parse_args()
    if a.accion == "crear":
        while True:
            print(f"Respaldo listo: {crear()}", flush=True)
            if not a.cada:
                break
            time.sleep(a.cada * 3600)
    elif a.accion == "listar":
        for p in respaldos():
            m = json.loads((p / "manifiesto.json").read_text(encoding="utf-8"))
            print(f"{p.name}  {m['reportes']} reportes, {m['archivos']} archivos")
    else:
        restaurar(a.carpeta)
        print(f"Restaurado desde {a.carpeta}. Inicie de nuevo el API.")
