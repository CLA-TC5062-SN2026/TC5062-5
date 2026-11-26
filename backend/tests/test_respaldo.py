"""RNF-14: el respaldo es una copia consistente de la base y las fotos, rota los antiguos y se puede restaurar."""

import sqlite3
import time

from app import config
from conftest import PNG
from scripts import respaldo


def contar_reportes():
    db = sqlite3.connect(config.DATABASE_PATH)
    try:
        return db.execute("SELECT COUNT(*) FROM reporte").fetchone()[0]
    finally:
        db.close()


def test_rnf14_respaldo_y_restauracion(condo, tmp_path):
    r = condo.reportar(fotos=[("rampa.png", PNG, "image/png")])
    assert r.status_code == 201, r.text
    antes = contar_reportes()
    carpeta = respaldo.crear(tmp_path)
    assert (carpeta / "reportaya.db").exists() and (carpeta / "fotos.tar.gz").exists()

    # Después del respaldo se pierde un reporte nuevo y las fotos; la restauración vuelve al estado respaldado.
    assert condo.reportar().status_code == 201
    assert contar_reportes() == antes + 1
    for archivo in config.UPLOAD_DIR.rglob("*.png"):
        archivo.unlink()
    respaldo.restaurar(carpeta)
    assert contar_reportes() == antes
    foto = r.json()["fotosAlta"][0]
    descarga = condo.get("inquilino", f"/reports/{r.json()['folio']}/files/{foto['id']}")
    assert descarga.status_code == 200 and descarga.content == PNG


def test_rnf14_conserva_solo_los_mas_recientes(condo, tmp_path):
    hechos = []
    for _ in range(3):
        hechos.append(respaldo.crear(tmp_path, conservar=2))
        time.sleep(1.05)  # el nombre de la carpeta lleva segundos
    (tmp_path / "notas").mkdir()  # lo que no es un respaldo no se cuenta ni se borra
    assert respaldo.respaldos(tmp_path) == [hechos[2], hechos[1]]
    assert not hechos[0].exists() and (tmp_path / "notas").exists()
