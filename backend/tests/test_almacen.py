"""RNF-08: las mismas reglas funcionan con el almacén local y con uno compatible con S3 (simulado con moto)."""

import boto3
import pytest
from moto import mock_aws

from app import almacen as A
from conftest import PNG


def folio_con_foto(condo):
    r = condo.reportar(fotos=[("rampa.png", PNG, "image/png")])
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def s3():
    with mock_aws():
        cliente = boto3.client("s3", region_name="us-east-1")
        cliente.create_bucket(Bucket="reportaya-pruebas")
        A.usar(A.AlmacenS3("reportaya-pruebas", "condominio", cliente=cliente))
        yield cliente
        A.usar(None)


def test_almacen_s3_alta_descarga_y_evidencia(condo, s3):
    d = folio_con_foto(condo)
    claves = [o["Key"] for o in s3.list_objects_v2(Bucket="reportaya-pruebas")["Contents"]]
    assert len(claves) == 1 and claves[0].startswith(f"condominio/{d['folio']}/")
    foto = d["fotosAlta"][0]
    r = condo.get("inquilino", f"/reports/{d['folio']}/files/{foto['id']}")
    assert r.status_code == 200 and r.content == PNG and r.headers["content-type"] == "image/png"
    condo.hasta_terminado(d["folio"])  # evidencia en S3 también
    assert s3.list_objects_v2(Bucket="reportaya-pruebas")["KeyCount"] == 2


def test_almacen_local_igual_contrato(condo):
    d = folio_con_foto(condo)
    r = condo.get("admin", f"/reports/{d['folio']}/files/{d['fotosAlta'][0]['id']}")
    assert r.status_code == 200 and r.content == PNG


def test_compensacion_si_la_operacion_falla(condo, s3, monkeypatch):
    """Si la transacción falla después de guardar el archivo, el archivo se borra del almacén."""
    from app import notificaciones

    def falla(*a, **k):
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(notificaciones, "al_alta", falla)
    with pytest.raises(RuntimeError):
        condo.reportar(fotos=[("x.png", PNG, "image/png")])
    assert s3.list_objects_v2(Bucket="reportaya-pruebas")["KeyCount"] == 0
    assert condo.get("admin", "/reports").json()["pagination"]["total"] == 0


def test_clave_fuera_de_la_carpeta_se_rechaza(tmp_path):
    local = A.AlmacenLocal(tmp_path)
    with pytest.raises(A.ArchivoNoEncontrado):
        local.leer("../../etc/passwd")
