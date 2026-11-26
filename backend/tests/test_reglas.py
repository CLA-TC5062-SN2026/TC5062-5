"""Pruebas de reglas de negocio: un caso por criterio de aceptación `RF-XX-AC-Y` de `S03_A1/SRS_equipo.md`.

    cd backend && python -m pytest tests/test_reglas.py -q

Usan el condominio de prueba del SRS (conftest.py) y fijan el reloj del sistema (RNF-10). Complementan a
`test_contrato.py`, que verifica códigos y esquemas contra el YAML con el servidor en marcha.
"""

import json

import pytest

from app import correo, notificaciones, reloj
from app.correo import CorreoNoEnviado
from app.db import connect
from conftest import PNG, hora


def folio_de(r):
    assert r.status_code == 201, r.text
    return r.json()["folio"]


def mensaje(r):
    return r.json()["mensaje"]


def bandeja(c, quien):
    return [a["mensaje"] for a in c.get(quien, "/notifications", params={"pageSize": 100}).json()["items"]]


# =============================================================== RF-01 Autenticación por rol
def test_rf01_ac1_sesion_con_rol_y_unidad(condo):
    r = condo.cliente.post("/api/v1/auth/login", json={"correo": "inquilino@ejemplo.com", "password": "Prueba1234"})
    assert r.status_code == 200
    assert r.json()["usuario"]["rol"] == "Residente" and r.json()["usuario"]["unidad"]["etiqueta"] == "B-502"


def test_rf01_ac2_contrasena_incorrecta_mismo_mensaje(condo):
    a = condo.cliente.post("/api/v1/auth/login", json={"correo": "inquilino@ejemplo.com", "password": "mala"})
    b = condo.cliente.post("/api/v1/auth/login", json={"correo": "nadie@ejemplo.com", "password": "mala"})
    assert a.status_code == b.status_code == 401 and mensaje(a) == mensaje(b) == "Correo o contraseña incorrectos"


def test_rf01_ac3_ac4_residente_y_vigilante_no_asignan_ni_cierran(condo):
    folio = folio_de(condo.reportar_en_unidad())
    assert condo.asignar(folio, quien="inquilino").status_code == 403
    f2 = folio_de(
        condo.reportar(
            "vigilante", medioOrigen="Caseta", fechaAviso="2026-09-21T08:00:00-06:00", nombreReferencia="Don Luis"
        )
    )
    assert condo.asignar(f2, quien="vigilante").status_code == 403
    assert condo.post("vigilante", f"/reports/{f2}/closures", json={}).status_code == 403
    assert condo.get("admin", f"/reports/{f2}").json()["estado"] == "Reportado"


def test_rnf06_bloqueo_tras_5_intentos(condo):
    for _ in range(5):
        condo.cliente.post("/api/v1/auth/login", json={"correo": "inquilino@ejemplo.com", "password": "mala"})
    r = condo.cliente.post("/api/v1/auth/login", json={"correo": "inquilino@ejemplo.com", "password": "Prueba1234"})
    assert r.status_code == 401  # bloqueada 15 minutos


def test_rnf06_token_renovado_en_cada_peticion(condo):
    assert "X-Token-Renovado" in condo.get("inquilino", "/auth/me").headers


def test_no_hay_registro_publico(condo):
    assert condo.cliente.post("/api/v1/auth/register", json={}).status_code == 404  # RF-02, EX-08


# =============================================================== RF-02 Padrón
def _alta_inquilino(condo, correo_="nuevo@ejemplo.com"):
    return condo.post(
        "admin",
        "/users",
        json={
            "nombre": "Nuevo Inquilino",
            "correo": correo_,
            "rol": "Residente",
            "vinculacion": {
                "unidadId": condo.id("A-402"),
                "ocupacion": "Inquilino",
                "fechaInicio": "2026-09-01T00:00:00-06:00",
            },
        },
    )


def test_rf02_ac1_alta_pendiente_y_enlace(condo):
    r = _alta_inquilino(condo)
    assert r.status_code == 201 and r.json()["estadoCuenta"] == "PendienteActivacion"
    assert "activar?token=" in condo.correos_a("nuevo@ejemplo.com")[0]


def test_rf02_ac2_correo_repetido(condo):
    r = _alta_inquilino(condo, "inquilino@ejemplo.com")
    assert r.status_code == 422 and mensaje(r) == "El correo ya está registrado"


def test_rf02_ac3_desactivado_no_entra_y_sus_reportes_siguen(condo):
    folio = folio_de(condo.reportar_en_unidad())
    u = condo.get("admin", f"/users/{condo.id('inquilino')}")
    assert (
        condo.patch(
            "admin", f"/users/{condo.id('inquilino')}", {"estadoCuenta": "Desactivada"}, u.headers["ETag"]
        ).status_code
        == 200
    )
    r = condo.cliente.post("/api/v1/auth/login", json={"correo": "inquilino@ejemplo.com", "password": "Prueba1234"})
    assert r.status_code == 401 and condo.get("admin", f"/reports/{folio}").status_code == 200


def test_rf02_ac4_ac7_proveedores_en_la_lista_de_responsables(condo):
    r = condo.post(
        "admin",
        "/users",
        json={
            "nombre": "Plomería Sur",
            "correo": "plomeria@ejemplo.com",
            "rol": "Mantenimiento",
            "mantenimiento": {"tipo": "ProveedorExterno", "especialidad": "Plomería", "telefono": "4430001111"},
        },
    )
    assert (
        r.status_code == 201
        and r.json()["estadoCuenta"] == "PendienteActivacion"
        and condo.correos_a("plomeria@ejemplo.com")
    )
    responsables = condo.get("admin", "/assignees").json()
    nombres = {x["nombre"]: x for x in responsables}
    assert "Plomería Sur" in nombres and nombres["Elevadores del Centro"]["sinAcceso"] is True


def test_rf02_ac5_ac6_unidad_sin_correo_ni_piso(condo):
    sin_correo = condo.post(
        "admin",
        "/units",
        json={"torre": "C", "piso": 1, "numero": "101", "propietario": {"nombre": "X", "viveEnCondominio": True}},
    )
    sin_piso = condo.post(
        "admin",
        "/units",
        json={
            "torre": "C",
            "numero": "102",
            "propietario": {"nombre": "X", "correo": "x@ejemplo.com", "viveEnCondominio": True},
        },
    )
    assert sin_correo.status_code == 422 and mensaje(sin_correo) == "El correo del propietario es obligatorio"
    assert sin_piso.status_code == 422 and mensaje(sin_piso) == "El piso es obligatorio"


def test_rf02_ac8_vigilancia_solo_captura(condo):
    folio_de(condo.reportar_en_unidad())
    assert condo.get("vigilante", "/reports").json()["pagination"]["total"] == 0
    assert condo.get("vigilante", "/users").status_code == 403


# =============================================================== RF-03 Alta por el residente
def test_rf03_ac1_folio_estado_fecha_y_medio(condo):
    condo.reportar()  # RY-000001
    r = condo.reportar()
    d = r.json()
    assert d["folio"] == "RY-000002" and d["estado"] == "Reportado" and d["medioOrigen"] == "Sistema"
    assert d["fechaAviso"].startswith("2026-09-21T09:00:00")


def test_rf03_ac2_descripcion_corta(condo):
    r = condo.reportar(descripcion="Fuga")
    assert r.status_code == 422 and mensaje(r) == "La descripción debe tener entre 10 y 1,000 caracteres"


def test_rf03_ac3_autorizacion_de_acceso(condo):
    r = condo.reportar_en_unidad(autorizaAcceso=...)
    assert r.status_code == 422 and mensaje(r) == "Indique si autoriza el acceso a su departamento"


def test_rf03_ac4_unidad_ajena(condo):
    r = condo.reportar_en_unidad(unidad="A-301")
    assert r.status_code == 422 and mensaje(r) == "Solo puede reportar en su unidad o en áreas comunes"


def test_rf03_ac6_peligro_obligatorio(condo):
    r = condo.reportar(esPeligroso=...)
    assert r.status_code == 422 and mensaje(r) == "Indique si el problema es peligroso o está empeorando"


def test_rf03_ac7_ac9_sin_fotos_y_opcionales(condo):
    a = condo.reportar()
    b = condo.reportar_en_unidad(desdeCuando="Desde ayer", habiaPasadoAntes=True, horariosAcceso="Tardes")
    assert a.status_code == b.status_code == 201
    assert b.json()["desdeCuando"] == "Desde ayer" and b.json()["habiaPasadoAntes"] is True


def test_rf03_ac8_parte_afectada(condo):
    d = condo.reportar_en_unidad().json()
    assert d["ubicacion"]["etiqueta"] == "B-502" and d["ubicacion"]["parteAfectada"] == "Baño"


def test_rf03_ac10_subtipo_obligatorio(condo):
    r = condo.reportar(subtipo=...)
    assert r.status_code == 422 and mensaje(r) == "Indique el subtipo"


# =============================================================== RF-04 Captura por terceros
def _captura(condo, quien="admin", **extra):
    base = dict(medioOrigen="Caseta", fechaAviso="2026-09-20T22:10:00-06:00", nombreReferencia="Guardia nocturno")
    base.update(extra)
    return condo.reportar(quien, **base)


def test_rf04_ac1_fecha_de_aviso_y_captura(condo):
    d = _captura(condo).json()
    assert (
        d["fechaAviso"].startswith("2026-09-20T22:10:00")
        and d["fechaCaptura"].startswith("2026-09-21T09:00:00")
        and d["medioOrigen"] == "Caseta"
    )


def test_rf04_ac2_aviso_futuro(condo):
    r = _captura(condo, fechaAviso="2026-09-21T10:00:00-06:00")
    assert r.status_code == 422 and mensaje(r) == "La fecha del aviso no puede ser futura"


def test_rf04_ac3_residente_reportante_ve_y_recibe_aviso(condo):
    folio = folio_de(
        _captura(
            condo,
            medioOrigen="WhatsApp",
            nombreReferencia=...,
            residenteReportanteId=condo.id("inquilino"),
            categoriaId=condo.cat("Plomería y fugas"),
            subtipo="Fuga activa",
            ubicacion={"tipo": "Unidad", "unidadId": condo.id("B-502")},
            autorizaAcceso=True,
        )
    )
    assert folio in [x["folio"] for x in condo.get("inquilino", "/reports").json()["items"]]
    assert any(folio in m for m in bandeja(condo, "inquilino"))


def test_rf04_ac4_autorizacion_del_ocupante(condo):
    r = _captura(
        condo,
        ubicacion={"tipo": "Unidad", "unidadId": condo.id("B-502")},
        categoriaId=condo.cat("Plomería y fugas"),
        subtipo="Otra",
    )
    assert r.status_code == 422 and mensaje(r) == "Indique si el ocupante autoriza el acceso"


def test_rf04_ac5_reportante_y_quien_capturo(condo):
    folio = folio_de(
        _captura(condo, "vigilante", nombreReferencia=..., residenteReportanteId=condo.id("residente_a301"))
    )
    d = condo.get("admin", f"/reports/{folio}").json()
    assert d["reportante"]["nombre"] == "Residente de A-301" and d["capturadoPor"]["nombre"] == "Vigilante"


def test_rf04_ac6_sin_nombre_de_referencia(condo):
    r = _captura(condo, nombreReferencia=...)
    assert r.status_code == 422 and mensaje(r) == "Indique el nombre de quien reporta"


def test_rf04_ac7_vigilante_solo_ve_los_suyos(condo):
    suyo = folio_de(_captura(condo, "vigilante"))
    folio_de(_captura(condo, "admin"))
    assert [x["folio"] for x in condo.get("vigilante", "/reports").json()["items"]] == [suyo]


def test_rf04_ac8_residente_no_captura_por_terceros(condo):
    assert condo.reportar(medioOrigen="WhatsApp").status_code == 403


def test_rf04_ac9_peligro_obligatorio(condo):
    r = _captura(condo, esPeligroso=...)
    assert r.status_code == 422 and mensaje(r) == "Indique si el problema es peligroso o está empeorando"


# =============================================================== RF-05 Fotografías y video
def test_rf05_ac1_a_ac3_fotos_validas_e_invalidas(condo):
    grande = b"\xff\xd8" + b"0" * (11 * 1024 * 1024)
    r = condo.reportar(
        fotos=[
            ("a.jpg", b"\xff\xd8" + b"0" * 100, "image/jpeg"),
            ("b.pdf", b"%PDF", "application/pdf"),
            ("c.jpg", grande, "image/jpeg"),
        ]
    )
    d = r.json()
    assert r.status_code == 201 and len(d["fotosAlta"]) == 1 and d["fotosAlta"][0]["etapa"] == "Alta"
    motivos = {x["nombre"]: x["motivo"] for x in d["archivosRechazados"]}
    assert motivos == {"b.pdf": "Formato no permitido: use JPEG o PNG", "c.jpg": "La foto supera 10 MB"}


def test_rf05_ac4_seis_fotos(condo):
    r = condo.reportar(fotos=[(f"{i}.png", PNG, "image/png") for i in range(6)])
    assert r.status_code == 422 and mensaje(r) == "Máximo 5 fotografías por etapa"
    assert condo.get("admin", "/reports").json()["pagination"]["total"] == 0


def test_rf05_ac5_ac6_video(condo):
    ok = condo.reportar(video=("v.mp4", b"0" * 1024, "video/mp4")).json()
    malo = condo.reportar(video=("w.mp4", b"0" * (51 * 1024 * 1024), "video/mp4")).json()
    archivos = condo.get("inquilino", f"/reports/{ok['folio']}/files").json()
    assert [a["tipo"] for a in archivos] == ["Video"]
    assert condo.get("inquilino", f"/reports/{ok['folio']}/files/{archivos[0]['id']}").status_code == 200
    assert malo["archivosRechazados"][0]["motivo"] == "El video supera 50 MB"


def test_rf05_ac7_nadie_borra_fotos(condo):
    d = condo.reportar(fotos=[("a.png", PNG, "image/png")]).json()
    fid = d["fotosAlta"][0]["id"]
    for quien in ("admin", "inquilino"):
        assert (
            condo.cliente.delete(f"/api/v1/reports/{d['folio']}/files/{fid}", headers=condo.como(quien)).status_code
            == 403
        )
    assert len(condo.get("admin", f"/reports/{d['folio']}/files").json()) == 1


# =============================================================== RF-06 Prioridad, asignación y reclasificación
def test_rf06_ac1_asignar(condo):
    folio = folio_de(condo.reportar())
    r = condo.asignar(folio, prioridad="Urgente")
    assert r.status_code == 201 and r.json()["estado"] == "Asignado"
    assert folio in [x["folio"] for x in condo.get("conserje", "/reports").json()["items"]]
    h = condo.get("admin", f"/reports/{folio}/history").json()["items"]
    assert any(
        x["tipo"] == "CambioEstado" and x.get("valorNuevo") == "Asignado" and x["autor"] == "Administrador" for x in h
    )


def test_rf06_ac2_ubicacion_de_origen_y_busqueda(condo):
    folio = folio_de(
        _captura(
            condo,
            categoriaId=condo.cat("Plomería y fugas"),
            subtipo="Fuga activa",
            autorizaAcceso=True,
            ubicacion={"tipo": "Unidad", "unidadId": condo.id("A-402")},
        )
    )
    condo.asignar(
        folio, ubicacionOrigen={"tipo": "Unidad", "unidadId": condo.id("A-502")}, responsableCosto="Condomino"
    )
    for unidad in ("A-402", "A-502"):
        items = condo.get("admin", "/reports", params={"ubicacionId": condo.id(unidad)}).json()["items"]
        assert [x["folio"] for x in items] == [folio]


def test_rf06_ac3_prioridad_obligatoria(condo):
    folio = folio_de(condo.reportar())
    r = condo.post("admin", f"/reports/{folio}/assignments", json={"responsableId": condo.id("conserje")})
    assert r.status_code == 422 and mensaje(r) == "La prioridad es obligatoria"
    assert condo.get("admin", f"/reports/{folio}").json()["estado"] == "Reportado"


def test_rf06_ac4_reasignar_en_proceso(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    condo.iniciar(folio)
    r = condo.patch("admin", f"/reports/{folio}/classification", {"responsableId": condo.id("bombas")})
    assert r.status_code == 200 and r.json()["estado"] == "EnProceso"
    assert condo.get("conserje", "/reports").json()["pagination"]["total"] == 0
    h = condo.get("admin", f"/reports/{folio}/history", params={"pageSize": 100}).json()["items"]
    assert any(
        x.get("campo") == "responsable"
        and x.get("valorAnterior") == "Conserje"
        and x.get("valorNuevo") == "Bombas del Norte"
        for x in h
    )


@pytest.mark.parametrize(
    "cat,sub,peligro,esperada",
    [
        ("Iluminación", "Pasillo o área techada", False, "Normal"),  # AC-5
        ("Iluminación", "Jardín o exterior", False, "Menor"),  # AC-6
        ("Plomería y fugas", "Fuga activa", False, "Urgente"),  # AC-7
        ("Iluminación", "Jardín o exterior", True, "Urgente"),
    ],
)
def test_rf06_ac5_a_ac7_prioridad_sugerida(condo, cat, sub, peligro, esperada):
    assert (
        condo.reportar(categoriaId=condo.cat(cat), subtipo=sub, esPeligroso=peligro).json()["prioridadSugerida"]
        == esperada
    )


def test_rf06_ac8_la_prioridad_final_es_de_la_administracion(condo):
    folio = folio_de(condo.reportar())  # sugerida Normal
    d = condo.asignar(folio, prioridad="Urgente").json()
    assert d["prioridad"] == "Urgente" and d["prioridadSugerida"] == "Normal"


def test_rf06_ac9_reclasificar_responsabilidad_avisa(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    r = condo.patch("admin", f"/reports/{folio}/classification", {"responsabilidad": "Privada"})
    assert r.status_code == 200 and r.json()["estado"] == "Asignado" and r.json()["responsabilidad"] == "Privada"
    assert any("Privada" in m for m in bandeja(condo, "inquilino"))


def test_rf06_ac10_proveedor_sin_acceso_no_genera_aviso(condo):
    folio = folio_de(condo.reportar())
    r = condo.asignar(folio, responsable="elevadores")
    assert r.status_code == 201 and r.json()["responsable"]["sinAcceso"] is True
    assert not any(folio in m for q in ("conserje", "bombas") for m in bandeja(condo, q))


# =============================================================== RF-07 Flujo de estados
def test_rf07_ac1_iniciar(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    assert condo.iniciar(folio).status_code == 201
    h = condo.get("conserje", f"/reports/{folio}/history").json()["items"]
    assert any(
        x.get("valorAnterior") == "Asignado" and x.get("valorNuevo") == "EnProceso" and x["autor"] == "Conserje"
        for x in h
    )


def test_rf07_ac2_reportado_a_terminado(condo):
    folio = folio_de(condo.reportar())
    r = condo.terminar(folio, quien="admin")
    assert r.status_code == 409 and mensaje(r) == "Transición no permitida"


def test_rf07_ac3_cancelado_y_unido_son_finales(condo):
    cancelado = folio_de(condo.reportar())
    condo.post("admin", f"/reports/{cancelado}/cancellations", json={"motivo": "Falsa alarma"})
    principal, unido = folio_de(condo.reportar()), folio_de(condo.reportar())
    assert condo.post("admin", f"/reports/{unido}/merges", json={"reportePrincipal": principal}).status_code == 201
    for folio in (cancelado, unido):
        assert condo.asignar(folio).status_code == 409
        assert condo.post("admin", f"/reports/{folio}/cancellations", json={"motivo": "x"}).status_code == 409


def test_rf07_ac4_otro_mantenimiento_recibe_404(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    assert condo.iniciar(folio, quien="bombas").status_code == 404


def test_rf07_ac5_cancelar_con_motivo(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    r = condo.post("admin", f"/reports/{folio}/cancellations", json={"motivo": ""})
    assert r.status_code == 422 and mensaje(r) == "El motivo es obligatorio"
    assert (
        condo.post("admin", f"/reports/{folio}/cancellations", json={"motivo": "Falsa alarma"}).json()["estado"]
        == "Cancelado"
    )


def test_rf07_ac6_residente_cancela_ya_resuelto(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    r = condo.post("inquilino", f"/reports/{folio}/cancellations", json={"motivo": "Ya se resolvió"})
    assert r.status_code == 201 and r.json()["estado"] == "Cancelado"
    assert any("Ya se resolvió" in m for m in bandeja(condo, "conserje")) and any(
        "Ya se resolvió" in m for m in bandeja(condo, "admin")
    )


def test_rf07_ac7_residente_no_cancela_en_proceso(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    condo.iniciar(folio)
    r = condo.post("inquilino", f"/reports/{folio}/cancellations", json={"motivo": "Ya se resolvió"})
    assert r.status_code == 409 and mensaje(r) == "Transición no permitida"


def test_rf07_ac8_cancelar_reporte_ajeno_404(condo):
    folio = folio_de(condo.reportar_en_unidad("residente_a301", unidad="A-301"))
    assert (
        condo.post("inquilino", f"/reports/{folio}/cancellations", json={"motivo": "Ya se resolvió"}).status_code == 404
    )


def test_rf07_ac9_motivo_distinto(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    r = condo.post("inquilino", f"/reports/{folio}/cancellations", json={"motivo": "Ya no me importa"})
    assert r.status_code == 422 and mensaje(r) == "Solo puede cancelar un reporte que ya se resolvió"


def test_rf07_ac10_en_nombre_de_proveedor_sin_acceso(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio, responsable="elevadores")
    r = condo.iniciar(folio, quien="admin", comentario="El proveedor confirmó que ya inició")
    assert r.status_code == 201
    h = condo.get("admin", f"/reports/{folio}/history").json()["items"]
    paso = next(x for x in h if x.get("valorNuevo") == "EnProceso")
    assert paso["actuaEnNombreDe"] == "Elevadores del Centro" and "Administrador" in paso["autor"]


# =============================================================== RF-08 Terminado con evidencia
def test_rf08_ac1_terminado_con_foto(condo):
    folio = folio_de(condo.reportar(fotos=[("alta.png", PNG, "image/png")]))
    condo.asignar(folio)
    condo.iniciar(folio)
    d = condo.terminar(folio).json()
    assert d["estado"] == "Terminado" and len(d["fotosAlta"]) == 1 and len(d["ciclos"][0]["fotosEvidencia"]) == 1
    assert d["ciclos"][0]["fotosEvidencia"][0]["etapa"] == "Evidencia"


def test_rf08_ac2_sin_fotos(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    condo.iniciar(folio)
    r = condo.terminar(folio, fotos=0)
    assert r.status_code == 422 and mensaje(r) == "Adjunte al menos una foto del trabajo terminado"
    assert condo.get("admin", f"/reports/{folio}").json()["estado"] == "EnProceso"


def test_rf08_ac3_cinco_fotos_por_ciclo(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    condo.iniciar(folio)
    condo.terminar(folio, fotos=5)
    condo.post("admin", f"/reports/{folio}/closures", json={})  # área común: se puede cerrar
    condo.post("admin", f"/reports/{folio}/reopenings", json={"comentario": "Volvió a fallar"})
    d = condo.terminar(folio, fotos=2).json()
    assert [len(c["fotosEvidencia"]) for c in d["ciclos"]] == [5, 2]


def test_rf08_ac4_ac5_sin_evidencia_para_proveedor_sin_acceso(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio, responsable="elevadores")
    condo.iniciar(folio, quien="admin")
    r = condo.terminar(folio, quien="admin", fotos=0, datos={"notaTrabajo": "x"})
    assert r.status_code == 422 and mensaje(r) == "Escriba la justificación"
    d = condo.terminar(
        folio,
        quien="admin",
        fotos=0,
        datos={"justificacionSinEvidencia": "El proveedor entregó solo la orden de servicio firmada"},
    ).json()
    assert d["estado"] == "Terminado" and d["ciclos"][0]["sinEvidenciaFotografica"] is True


def test_rf08_ac6_la_excepcion_no_aplica_al_personal_propio(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    condo.iniciar(folio)
    r = condo.terminar(folio, quien="admin", fotos=0, datos={"justificacionSinEvidencia": "No hubo cámara"})
    assert r.status_code == 422 and mensaje(r) == "Adjunte al menos una foto del trabajo terminado"


def test_rf08_ac7_pendientes_en_el_historial(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    condo.iniciar(folio)
    d = condo.terminar(folio, datos={"pendientes": "Falta cambiar el balastro"}).json()
    assert d["estado"] == "Terminado"
    h = condo.get("admin", f"/reports/{folio}/history").json()["items"]
    assert any("Falta cambiar el balastro" in (x.get("comentario") or "") for x in h)


# =============================================================== RF-09 Confirmación y cierre
def _terminado_b502(condo):
    reloj.fijar(hora("22/09/2026 10:00"))
    folio = folio_de(condo.reportar_en_unidad())
    condo.hasta_terminado(folio)
    return folio


def test_rf09_ac1_ya_quedo_y_cierre(condo):
    folio = _terminado_b502(condo)
    reloj.fijar(hora("22/09/2026 18:00"))
    assert (
        condo.post("inquilino", f"/reports/{folio}/resident-responses", json={"respuesta": "YaQuedo"}).status_code
        == 201
    )
    assert condo.post("admin", f"/reports/{folio}/closures", json={}).json()["estado"] == "Cerrado"


def test_rf09_ac2_esperando_confirmacion(condo):
    folio = _terminado_b502(condo)
    reloj.fijar(hora("22/09/2026 20:00"))
    r = condo.post("admin", f"/reports/{folio}/closures", json={})
    assert r.status_code == 409 and mensaje(r) == "Esperando confirmación del residente hasta el 25/09/2026 10:00"


def test_rf09_ac3_plazo_vencido_para_responder_y_cierre(condo):
    folio = _terminado_b502(condo)
    reloj.fijar(hora("25/09/2026 10:01"))
    r = condo.post("inquilino", f"/reports/{folio}/resident-responses", json={"respuesta": "YaQuedo"})
    assert r.status_code == 409 and mensaje(r) == "El plazo para responder terminó"
    assert condo.post("admin", f"/reports/{folio}/closures", json={}).status_code == 201  # (b) pasaron 72 h


def test_rf09_ac4_sigue_fallando_exige_motivo(condo):
    folio = _terminado_b502(condo)
    condo.post(
        "inquilino",
        f"/reports/{folio}/resident-responses",
        json={"respuesta": "SigueFallando", "comentario": "Volvió a gotear"},
    )
    r = condo.post("admin", f"/reports/{folio}/closures", json={})
    assert r.status_code == 422 and mensaje(r) == "Escriba el motivo del cierre"
    assert (
        condo.post(
            "admin", f"/reports/{folio}/closures", json={"motivo": "Es otra fuga; se abre reporte nuevo"}
        ).status_code
        == 201
    )


def test_rf09_ac5_reabrir_con_ciclo_nuevo(condo):
    folio = _terminado_b502(condo)
    condo.post(
        "inquilino",
        f"/reports/{folio}/resident-responses",
        json={"respuesta": "SigueFallando", "comentario": "Volvió a gotear"},
    )
    d = condo.post(
        "admin", f"/reports/{folio}/reopenings", json={"comentario": "Se revisará de nuevo la tubería"}
    ).json()
    assert d["folio"] == folio and d["estado"] == "EnProceso" and len(d["ciclos"]) == 2
    assert d["ciclos"][0]["confirmacion"]["respuesta"] == "SigueFallando"


def test_rf09_ac6_area_comun_se_cierra_sin_esperar(condo):
    folio = folio_de(condo.reportar())
    condo.hasta_terminado(folio)
    reloj.avanzar(hours=1)
    assert condo.post("admin", f"/reports/{folio}/closures", json={}).json()["estado"] == "Cerrado"


def test_rf09_ac7_ac8_mantenimiento_y_residente_no_cierran(condo):
    folio = _terminado_b502(condo)
    assert condo.post("conserje", f"/reports/{folio}/closures", json={}).status_code == 403
    assert condo.post("inquilino", f"/reports/{folio}/closures", json={}).status_code == 403
    assert condo.get("admin", f"/reports/{folio}").json()["estado"] == "Terminado"


def test_rf09_ac9_reportante_sin_cuenta(condo):
    folio = folio_de(
        _captura(
            condo,
            categoriaId=condo.cat("Plomería y fugas"),
            subtipo="Otra",
            autorizaAcceso=True,
            ubicacion={"tipo": "Unidad", "unidadId": condo.id("B-502")},
        )
    )
    condo.hasta_terminado(folio)
    assert condo.post("admin", f"/reports/{folio}/closures", json={}).json()["estado"] == "Cerrado"


def test_rf27_ac4_plazo_de_confirmacion_configurable(condo):
    condo.put("admin", "/parameters/plazoConfirmacionHoras", {"valor": 96})
    folio = _terminado_b502(condo)
    assert (
        condo.get("admin", f"/reports/{folio}")
        .json()["ciclos"][0]["plazoConfirmacionHasta"]
        .startswith("2026-09-26T10:00:00")
    )


# =============================================================== RF-10 Consulta del residente
def test_rf10_ac1_su_unidad_y_areas_comunes(condo):
    propios = [folio_de(condo.reportar_en_unidad()) for _ in range(2)]
    comunes = [folio_de(condo.reportar("residente_a301")) for _ in range(3)]
    folio_de(condo.reportar_en_unidad("residente_a301", unidad="A-301"))  # de otra unidad: no
    items = condo.get("inquilino", "/reports", params={"pageSize": 100}).json()["items"]
    assert sorted(x["folio"] for x in items) == sorted(propios + comunes)


def test_rf10_ac2_otra_unidad_404(condo):
    folio = folio_de(condo.reportar_en_unidad("residente_a301", unidad="A-301"))
    assert condo.get("inquilino", f"/reports/{folio}").status_code == 404


def test_rf10_ac3_area_comun_sin_reportante(condo):
    folio = folio_de(condo.reportar("residente_a301"))
    d = condo.get("inquilino", f"/reports/{folio}").json()
    assert "reportante" not in d and d["categoria"] == "Iluminación" and "descripcion" in d and "fechaAviso" in d


def test_rf10_ac4_reportes_anteriores_a_su_vinculacion(condo):
    reloj.fijar(hora("01/03/2026 10:00"))
    anterior = folio_de(
        _captura(
            condo,
            categoriaId=condo.cat("Plomería y fugas"),
            subtipo="Fuga activa",
            autorizaAcceso=True,
            fechaAviso="2026-03-01T09:00:00-06:00",
            ubicacion={"tipo": "Unidad", "unidadId": condo.id("B-502")},
        )
    )
    condo.sql(
        "UPDATE vinculacion_unidad SET fecha_inicio='2026-06-01T06:00:00Z' WHERE residente_id=?", condo.id("inquilino")
    )
    reloj.fijar(hora("21/09/2026 09:00"))
    assert anterior not in [x["folio"] for x in condo.get("inquilino", "/reports").json()["items"]]


def test_rf10_ac5_unido_a(condo):
    principal = folio_de(condo.reportar("residente_a301"))
    suyo = folio_de(condo.reportar())
    condo.post("admin", f"/reports/{suyo}/merges", json={"reportePrincipal": principal})
    d = condo.get("inquilino", f"/reports/{suyo}").json()
    assert d["estado"] == "Unido" and d["reportePrincipal"] == principal


def test_rf10_ac6_detenido_con_motivo(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    condo.iniciar(folio)
    condo.post("conserje", f"/reports/{folio}/holds", json={"motivo": "EsperaDePieza"})
    d = condo.get("inquilino", f"/reports/{folio}").json()
    assert d["detenido"] is True and d["detencionAbierta"]["motivo"] == "EsperaDePieza"


def test_rnf05_el_residente_no_ve_datos_confidenciales(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    condo.post("conserje", f"/reports/{folio}/notes", json={"texto": "Falta la pieza; llega el jueves"})
    condo.post("admin", f"/reports/{folio}/costs", json={"monto": 1200, "pagador": "Condomino"})
    d = condo.get("inquilino", f"/reports/{folio}").json()
    assert {"notas", "montoCosto", "propietario", "responsable", "capturadoPor"}.isdisjoint(
        d
    )  # RF-15-AC-3, RF-20-AC-5, RF-24-AC-3
    assert d["pagador"] == "Condomino"  # RF-20-AC-5: sí ve el pagador


# =============================================================== RF-11 Avisos
def test_rf11_ac1_alta(condo):
    folio = folio_de(condo.reportar_en_unidad())
    assert any(folio in m for m in bandeja(condo, "inquilino")) and any(
        f"Reporte nuevo {folio}" in m for m in bandeja(condo, "admin")
    )
    assert any(folio in t for t in condo.correos_a("inquilino@ejemplo.com"))


def test_rf11_ac2_propietario_no_residente_solo_correo(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio, responsableCosto="Condomino")
    correo_prop = [t for t in condo.correos_a("pedro.propietario@ejemplo.com") if "Asignado" in t]
    assert correo_prop and folio in correo_prop[0] and "condómino" in correo_prop[0]


def test_rf11_ac3_area_comun_sin_propietarios(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    destinos = [
        r["destinatario"]
        for r in condo.sql(
            "SELECT e.destinatario FROM envio_correo e JOIN aviso a ON a.id=e.aviso_id WHERE a.reporte_folio=?", folio
        )
    ]
    assert not any(d in destinos for d in ("pedro.propietario@ejemplo.com", "alicia@ejemplo.com", "oscar@ejemplo.com"))


def test_rf11_ac4_correo_fallido_tras_3_intentos(condo):
    class Caido:
        def enviar(self, *a):
            raise CorreoNoEnviado("sin respuesta")

    correo.usar(Caido())
    folio = folio_de(condo.reportar())
    assert condo.get("admin", f"/reports/{folio}").json()["estado"] == "Reportado"  # el cambio se guardó
    assert bandeja(condo, "inquilino")  # y el aviso en el sistema también
    for minutos in (10, 10):
        reloj.avanzar(minutes=minutos)
        db = connect()
        notificaciones.procesar_correos(db)
        db.close()
    fallidos = condo.get("admin", "/email-deliveries", params={"estado": "Fallido"}).json()["items"]
    assert fallidos and all(x["intentos"] == 3 for x in fallidos)


def test_rf11_ac5_aviso_al_responsable(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio, prioridad="Urgente")
    assert any(folio in m and "Urgente" in m for m in bandeja(condo, "conserje"))


def test_rf11_ac6_cancelacion_por_el_residente(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    condo.post("inquilino", f"/reports/{folio}/cancellations", json={"motivo": "Ya se resolvió"})
    assert any(folio in t and "Ya se resolvió" in t for t in condo.correos_a("conserje@ejemplo.com"))


def test_rf11_ac7_en_proceso_no_avisa_al_residente(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    antes = len(bandeja(condo, "inquilino"))
    condo.iniciar(folio)
    condo.post("conserje", f"/reports/{folio}/notes", json={"texto": "Revisé la llave de paso"})
    assert len(bandeja(condo, "inquilino")) == antes


def test_rf11_ac8_sin_cuenta_a_la_administracion(condo):
    folio = folio_de(_captura(condo))
    condo.asignar(folio)
    assert any(folio in m and "comuníqueselo manualmente" in m for m in bandeja(condo, "admin"))


def test_rf11_ac9_correo_de_terminado_con_plazo(condo):
    folio = _terminado_b502(condo)
    assert any(
        folio in t and "Ya quedó" in t and "25/09/2026 10:00" in t for t in condo.correos_a("inquilino@ejemplo.com")
    )


def test_rf11_constancia_en_el_historial(condo):
    folio = folio_de(condo.reportar_en_unidad())
    h = condo.get("admin", f"/reports/{folio}/history").json()["items"]
    assert any(x["tipo"] == "AvisoEnviado" and x.get("canal") in ("Sistema", "Correo") for x in h)


# =============================================================== RF-12 Historial y búsqueda
def test_rf12_ac1_rango_inclusivo_y_orden(condo):
    fechas = ["2025-12-15T10:00:00", "2026-01-01T10:00:00", "2026-06-30T23:30:00", "2026-07-01T10:00:00"]
    for f in fechas:
        _captura(condo, categoriaId=condo.cat("Bombas y cisterna"), subtipo="Otra", fechaAviso=f + "-06:00")
    items = condo.get(
        "admin",
        "/reports",
        params={"categoriaId": condo.cat("Bombas y cisterna"), "avisoDesde": "2026-01-01", "avisoHasta": "2026-06-30"},
    ).json()["items"]
    assert [x["fechaAviso"][:10] for x in items] == ["2026-06-30", "2026-01-01"]


def test_rf12_ac3_detalle_con_ciclos(condo):
    folio = folio_de(condo.reportar(fotos=[("a.png", PNG, "image/png")]))
    condo.hasta_terminado(folio)
    condo.post("admin", f"/reports/{folio}/closures", json={})
    condo.post("admin", f"/reports/{folio}/reopenings", json={"comentario": "Volvió a fallar"})
    condo.terminar(folio)
    d = condo.get("admin", f"/reports/{folio}").json()
    assert len(d["fotosAlta"]) == 1 and [len(c["fotosEvidencia"]) for c in d["ciclos"]] == [1, 1]


def test_rf12_ac4_texto(condo):
    a = folio_de(condo.reportar(descripcion="Hay una gotera en el techo"))
    folio_de(condo.reportar(descripcion="Lámpara fundida en la rampa"))
    assert [x["folio"] for x in condo.get("admin", "/reports", params={"texto": "gotera"}).json()["items"]] == [a]


def test_rf12_ac5_residente_no_busca(condo):
    assert condo.get("inquilino", "/reports", params={"texto": "gotera"}).status_code == 403


# =============================================================== RF-13 Tablero
def _urgente_con_tiempos(condo, aviso, primera_min, resolucion_h, responsable="conserje"):
    reloj.fijar(hora(aviso))
    folio = folio_de(condo.reportar(categoriaId=condo.cat("Electricidad"), subtipo="Riesgo eléctrico"))
    condo.asignar(folio, responsable=responsable)
    reloj.avanzar(minutes=primera_min)
    condo.iniciar(folio, quien=responsable)
    reloj.fijar(hora(aviso))
    reloj.avanzar(hours=resolucion_h)
    condo.terminar(folio, quien=responsable)
    return folio


def test_rf13_ac1_promedios_y_cumplimiento(condo):
    for dia, pm, rh in (("05", 30, 10), ("10", 50, 20), ("15", 130, 36)):
        _urgente_con_tiempos(condo, f"{dia}/09/2026 08:00", pm, rh)
    reloj.fijar(hora("01/10/2026 09:00"))
    t = condo.get("admin", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).json()
    u = next(p for p in t["porPrioridad"] if p["prioridad"] == "Urgente")
    assert (
        u["primeraAtencionPromedioMin"] == 70 and u["cumplimientoPrimeraAtencion"]["personalPropio"]["porcentaje"] == 67
    )
    assert u["resolucionPromedioHoras"] == 22 and u["cumplimientoResolucion"]["personalPropio"]["porcentaje"] == 67


def test_rf13_ac2_ac3_recurrentes(condo):
    folios = []
    for f in ("2026-07-15", "2026-08-15", "2026-09-20"):
        folios.append(folio_de(_captura(condo, fechaAviso=f + "T10:00:00-06:00")))
    reloj.fijar(hora("03/10/2026 09:00"))
    t = condo.get("admin", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).json()
    assert t["recurrentes"] == [
        {"categoria": "Iluminación", "ubicacionOrigen": "Rampa del estacionamiento", "folios": folios}
    ]
    condo.post("admin", f"/reports/{folios[0]}/cancellations", json={"motivo": "Duplicado"})
    assert (
        condo.get("admin", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).json()["recurrentes"]
        == []
    )


def test_rf13_ac4_incumplido_por_vencimiento(condo):
    folio_de(
        _captura(condo, categoriaId=condo.cat("Otro"), subtipo=..., fechaAviso="2026-09-20T10:00:00-06:00")
    )  # Normal
    reloj.fijar(hora("23/09/2026 11:00"))
    t = condo.get("admin", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).json()
    n = next(p for p in t["porPrioridad"] if p["prioridad"] == "Normal")
    assert n["cumplimientoResolucion"]["personalPropio"] == {"reportes": 1, "cumplen": 0, "porcentaje": 0}


def test_rf13_ac5_tiempo_detenido(condo):
    reloj.fijar(hora("09/09/2026 08:00"))
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    condo.iniciar(folio)
    reloj.fijar(hora("10/09/2026 09:00"))
    hold = condo.post("conserje", f"/reports/{folio}/holds", json={"motivo": "EsperaDePieza"}).json()
    reloj.fijar(hora("12/09/2026 09:00"))
    condo.cliente.patch(
        f"/api/v1/reports/{folio}/holds/{hold['id']}",
        headers={**condo.como("conserje"), "Content-Type": "application/merge-patch+json"},
        content=json.dumps({"reanudada": True}),
    )
    t = condo.get("admin", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).json()
    assert t["detenciones"] == [{"folio": folio, "horasDetenido": 48, "motivos": ["Espera de pieza"]}]


def test_rf13_ac6_adopcion(condo):
    reloj.fijar(hora("20/10/2026 09:00"))
    for _ in range(6):
        condo.reportar()
    for _ in range(4):
        _captura(condo, medioOrigen="WhatsApp", fechaAviso="2026-10-20T08:00:00-06:00")
    t = condo.get("admin", "/metrics", params={"desde": "2026-10-01", "hasta": "2026-10-31"}).json()
    assert t["adopcionPorcentaje"] == 60


def test_rf13_ac7_bloque_de_proveedores_externos(condo):
    for dia in ("05", "06"):
        _urgente_con_tiempos(condo, f"{dia}/09/2026 08:00", 30, 10, responsable="bombas")
    t = condo.get("admin", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).json()
    u = next(p for p in t["porPrioridad"] if p["prioridad"] == "Urgente")["cumplimientoResolucion"]
    assert u["proveedoresExternos"]["reportes"] == 2 and u["personalPropio"]["reportes"] == 0


def test_rf13_ac8_residente_403(condo):
    assert condo.get("inquilino", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).status_code == 403


def test_rf27_ac1_el_tablero_usa_el_objetivo_nuevo(condo):
    _urgente_con_tiempos(condo, "05/09/2026 08:00", 30, 20)
    condo.put("admin", "/parameters/objetivoResolucionUrgenteHoras", {"valor": 12})
    t = condo.get("admin", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).json()
    u = next(p for p in t["porPrioridad"] if p["prioridad"] == "Urgente")
    assert u["cumplimientoResolucion"]["personalPropio"]["porcentaje"] == 0  # 20 h > 12 h
    cambio = condo.get("admin", "/parameters/objetivoResolucionUrgenteHoras/changes").json()[0]
    assert (cambio["valorAnterior"], cambio["valorNuevo"], cambio["usuario"]) == (24, 12, "Administrador")


# =============================================================== RF-14 Activación y recuperación
def _token(condo, destinatario):
    import re

    return re.search(r"token=([A-Za-z0-9_-]+)", condo.correos_a(destinatario)[-1]).group(1)


def test_rf14_ac1_activar_un_solo_uso(condo):
    _alta_inquilino(condo)
    tok = _token(condo, "nuevo@ejemplo.com")
    assert (
        condo.cliente.post("/api/v1/account-activations", json={"token": tok, "password": "Segura123"}).status_code
        == 204
    )
    assert (
        condo.cliente.post(
            "/api/v1/auth/login", json={"correo": "nuevo@ejemplo.com", "password": "Segura123"}
        ).status_code
        == 200
    )
    assert (
        condo.cliente.post("/api/v1/account-activations", json={"token": tok, "password": "Segura123"}).status_code
        == 422
    )


def test_rf14_ac2_enlace_vencido(condo):
    reloj.fijar(hora("20/09/2026 10:00"))
    _alta_inquilino(condo)
    tok = _token(condo, "nuevo@ejemplo.com")
    reloj.fijar(hora("23/09/2026 10:01"))
    r = condo.cliente.post("/api/v1/account-activations", json={"token": tok, "password": "Segura123"})
    assert r.status_code == 422 and mensaje(r) == "El enlace venció; pida uno nuevo a la Administración"
    uid = condo.sql("SELECT id FROM usuario WHERE correo='nuevo@ejemplo.com'")[0]["id"]
    assert condo.post("admin", f"/users/{uid}/activation-links").status_code == 202
    assert (
        condo.cliente.post(
            "/api/v1/account-activations", json={"token": _token(condo, "nuevo@ejemplo.com"), "password": "Segura123"}
        ).status_code
        == 204
    )


def test_rf14_ac3_recuperacion_respuesta_uniforme_y_1_hora(condo):
    a = condo.cliente.post("/api/v1/password-reset-requests", json={"correo": "inquilino@ejemplo.com"})
    b = condo.cliente.post("/api/v1/password-reset-requests", json={"correo": "nadie@ejemplo.com"})
    assert a.status_code == b.status_code == 202 and a.json() == b.json()
    tok = _token(condo, "inquilino@ejemplo.com")
    reloj.avanzar(minutes=61)
    assert (
        condo.cliente.post("/api/v1/password-resets", json={"token": tok, "password": "Nueva1234"}).status_code == 422
    )


def test_rf14_ac4_comando_de_arranque(condo, tmp_path, monkeypatch):
    from scripts import init_db

    condo.sql("PRAGMA foreign_keys = OFF")
    for t in (
        "vinculacion_unidad",
        "residente",
        "vigilante",
        "usuario_mantenimiento",
        "usuario_administracion",
        "usuario",
    ):
        condo.sql(f"DELETE FROM {t}")
    init_db.primer_administrador("ana@condominio.mx", "Ana López")
    u = condo.sql(
        "SELECT u.estado_cuenta, a.perfil_administracion FROM usuario u JOIN usuario_administracion a ON a.usuario_id=u.id"
    )
    assert [tuple(x) for x in u] == [("PendienteActivacion", "Administrador")] and condo.correos_a("ana@condominio.mx")


# =============================================================== RF-15 Notas y visita
def test_rf15_ac1_nota_interna(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    condo.iniciar(folio)
    n = condo.post("conserje", f"/reports/{folio}/notes", json={"texto": "Falta la pieza; llega el jueves"})
    assert n.status_code == 201 and n.json()["autor"] == "Conserje"
    assert condo.get("admin", f"/reports/{folio}").json()["estado"] == "EnProceso"


def test_rf15_ac2_visita_visible_y_avisada(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    r = condo.put("admin", f"/reports/{folio}/visit", {"fechaVisita": "2026-09-29T10:00:00-06:00"})
    assert r.status_code == 200
    assert condo.get("inquilino", f"/reports/{folio}").json()["fechaVisita"].startswith("2026-09-29T10:00:00")
    assert any("29/09/2026 10:00" in m for m in bandeja(condo, "inquilino"))


# =============================================================== RF-16 Lista de Mantenimiento
def test_rf16_ac1_ac3_orden(condo):
    folios = {}
    for clave, prio, aviso in (
        ("normal_20", "Normal", "2026-09-20"),
        ("urgente_22", "Urgente", "2026-09-22"),
        ("normal_18", "Normal", "2026-09-18"),
        ("normal_21", "Normal", "2026-09-21"),
    ):
        reloj.fijar(hora("23/09/2026 09:00"))
        f = folio_de(_captura(condo, fechaAviso=f"{aviso}T08:00:00-06:00"))
        condo.asignar(f, prioridad=prio)
        folios[clave] = f
    orden = [x["folio"] for x in condo.get("conserje", "/reports").json()["items"]]
    assert orden == [folios["urgente_22"], folios["normal_18"], folios["normal_20"], folios["normal_21"]]


def test_rf16_ac2_ajenos_y_cerrados_no_aparecen(condo):
    ajeno = folio_de(condo.reportar())
    condo.asignar(ajeno, responsable="bombas")
    cerrado = folio_de(condo.reportar())
    condo.hasta_terminado(cerrado)
    condo.post("admin", f"/reports/{cerrado}/closures", json={})
    assert condo.get("conserje", "/reports").json()["items"] == []


def test_rf16_ac4_sin_autorizacion_de_acceso(condo):
    folio = folio_de(condo.reportar_en_unidad(autorizaAcceso=False))
    condo.asignar(folio)
    item = condo.get("conserje", "/reports").json()["items"][0]
    assert item["mensajeAcceso"] == "Sin autorización de acceso: coordinar con la Administración"
    assert condo.get("conserje", f"/reports/{folio}").json()["mensajeAcceso"] == item["mensajeAcceso"]


# =============================================================== Segunda fase (RF-17 a RF-26)
def test_rf17_duplicados(condo):
    a = folio_de(condo.reportar_en_unidad())
    b = condo.reportar_en_unidad("residente_a301", unidad="A-301").json()  # torre A: no es duplicado
    reloj.avanzar(minutes=1)
    c = condo.reportar(
        "admin",
        categoriaId=condo.cat("Plomería y fugas"),
        subtipo="Otra",
        medioOrigen="Llamada",
        fechaAviso="2026-09-21T08:30:00-06:00",
        nombreReferencia="Vecino",
        autorizaAcceso=True,
        ubicacion={"tipo": "Unidad", "unidadId": condo.id("B-502")},
    ).json()
    assert b["posibleDuplicado"] is False and c["posibleDuplicado"] is True  # AC-1, AC-5
    assert any(f"posible duplicado de {a}" in m for m in bandeja(condo, "admin"))


def test_rf18_detenida(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.asignar(folio)
    condo.iniciar(folio)
    r = condo.post("conserje", f"/reports/{folio}/holds", json={})
    assert r.status_code == 422 and mensaje(r) == "Indique el motivo de la detención"  # AC-2
    h = condo.post("conserje", f"/reports/{folio}/holds", json={"motivo": "EsperaDePieza"}).json()
    assert condo.get("admin", f"/reports/{folio}").json()["estado"] == "EnProceso"  # AC-1
    assert any("Espera de pieza" in m for m in bandeja(condo, "inquilino"))  # AC-5
    condo.cliente.patch(
        f"/api/v1/reports/{folio}/holds/{h['id']}",
        headers={**condo.como("conserje"), "Content-Type": "application/merge-patch+json"},
        content=json.dumps({"reanudada": True}),
    )
    assert condo.get("admin", f"/reports/{folio}").json()["detenido"] is False  # AC-3
    condo.terminar(folio)
    assert (
        condo.post("conserje", f"/reports/{folio}/holds", json={"motivo": "Otro", "textoOtro": "x"}).status_code == 409
    )  # AC-4


def test_rf19_persistencia_y_reapertura_de_un_cerrado(condo):
    folio = _terminado_b502(condo)
    condo.post("inquilino", f"/reports/{folio}/resident-responses", json={"respuesta": "YaQuedo"})
    reloj.fijar(hora("01/10/2026 10:00"))
    condo.post("admin", f"/reports/{folio}/closures", json={})
    reloj.fijar(hora("10/10/2026 10:00"))
    assert condo.post("inquilino", f"/reports/{folio}/persistence-indications", json={}).status_code == 201  # AC-1
    assert condo.get("admin", f"/reports/{folio}").json()["estado"] == "Cerrado"  # AC-2
    r = condo.post("admin", f"/reports/{folio}/reopenings", json={"comentario": ""})
    assert r.status_code == 422 and mensaje(r) == "Escriba el motivo de la reapertura"  # AC-5
    d = condo.post("admin", f"/reports/{folio}/reopenings", json={"comentario": "Sigue la humedad"}).json()
    assert d["estado"] == "EnProceso" and d["folio"] == folio and len(d["ciclos"]) == 2  # AC-3
    reloj.fijar(hora("31/10/2026 10:01"))


def test_rf19_ac4_plazo_para_reabrir(condo):
    folio = _terminado_b502(condo)
    condo.post("inquilino", f"/reports/{folio}/resident-responses", json={"respuesta": "YaQuedo"})
    reloj.fijar(hora("01/10/2026 10:00"))
    condo.post("admin", f"/reports/{folio}/closures", json={})
    reloj.fijar(hora("31/10/2026 10:01"))
    r = condo.post("inquilino", f"/reports/{folio}/persistence-indications", json={})
    assert r.status_code == 409 and mensaje(r) == "El plazo para reabrir terminó"


def test_rf20_costo_y_pagador(condo):
    folio = folio_de(condo.reportar_en_unidad())
    c = condo.post("admin", f"/reports/{folio}/costs", json={"monto": 2500, "pagador": "Condominio"}).json()
    r = condo.post("admin", f"/reports/{folio}/costs", json={"monto": -1, "pagador": "Condominio"})
    assert r.status_code == 422 and mensaje(r) == "El monto no puede ser negativo"  # AC-3
    condo.post(
        "admin", f"/reports/{folio}/costs", json={"monto": 2300, "pagador": "Condominio", "anulaCostoId": c["id"]}
    )
    d = condo.get("admin", f"/reports/{folio}").json()
    assert d["montoCosto"] == 2300 and len(condo.get("admin", f"/reports/{folio}/costs").json()) == 2  # AC-4


def test_rf21_delegacion_a_la_auxiliar(condo):
    folio = folio_de(condo.reportar())
    assert condo.asignar(folio, quien="auxiliar").status_code == 403  # AC-2
    d = condo.post(
        "admin", "/delegations", json={"auxiliarId": condo.id("auxiliar"), "fechaFin": "2026-10-05T23:59:00-06:00"}
    ).json()
    assert condo.asignar(folio, quien="auxiliar").status_code == 201  # AC-1
    h = condo.get("admin", f"/reports/{folio}/history").json()["items"]
    assert any(x.get("valorNuevo") == "Asignado" and x["autor"] == "Auxiliar" for x in h)  # AC-4
    otro = folio_de(condo.reportar())
    reloj.fijar(hora("06/10/2026 08:00"))
    assert condo.asignar(otro, quien="auxiliar").status_code == 403  # AC-5
    reloj.fijar(hora("21/09/2026 09:00"))
    condo.cliente.patch(
        f"/api/v1/delegations/{d['id']}",
        headers={**condo.como("admin"), "Content-Type": "application/merge-patch+json"},
        content=json.dumps({"habilitada": False}),
    )
    assert condo.asignar(otro, quien="auxiliar").status_code == 403  # AC-3
    assert condo.put("auxiliar", "/parameters/plazoConfirmacionHoras", {"valor": 48}).status_code == 403  # RF-27-AC-3


def test_rf22_estancado_una_sola_vez(condo):
    reloj.fijar(hora("21/09/2026 08:00"))
    folio = folio_de(condo.reportar(categoriaId=condo.cat("Electricidad"), subtipo="Riesgo eléctrico"))  # Urgente
    reloj.fijar(hora("21/09/2026 10:01"))
    db = connect()
    assert notificaciones.revisar_estancados(db) == 1  # AC-1
    reloj.avanzar(hours=1)
    assert notificaciones.revisar_estancados(db) == 0  # AC-2
    db.close()
    assert any(folio in m and "sin moverse" in m for m in bandeja(condo, "admin"))


def test_rf23_pdf_con_las_mismas_cifras(condo):
    _urgente_con_tiempos(condo, "05/09/2026 08:00", 30, 22)
    r = condo.get(
        "admin",
        "/metrics",
        params={"desde": "2026-09-01", "hasta": "2026-09-30"},
        headers={"Accept": "application/pdf"},
    )
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    assert (
        condo.get(
            "inquilino",
            "/metrics",
            params={"desde": "2026-09-01", "hasta": "2026-09-30"},
            headers={"Accept": "application/pdf"},
        ).status_code
        == 403
    )  # AC-3


def test_rf24_propietario_solo_para_la_administracion(condo):
    folio = folio_de(condo.reportar_en_unidad())
    assert (
        condo.get("admin", f"/reports/{folio}").json()["propietario"]["correo"] == "pedro.propietario@ejemplo.com"
    )  # AC-2
    assert "propietario" not in condo.get("inquilino", f"/reports/{folio}").json()  # AC-3


def test_rf25_garantia(condo):
    folio = folio_de(condo.reportar())
    condo.asignar(folio)
    condo.iniciar(folio)
    r = condo.terminar(folio, datos={"garantiaVencimiento": "2026-09-01"})
    assert r.status_code == 422 and mensaje(r) == "La fecha de vencimiento no puede ser pasada"  # AC-2
    d = condo.terminar(folio, datos={"garantiaVencimiento": "2027-09-30"}).json()
    assert d["ciclos"][0]["garantiaVencimiento"] == "2027-09-30"  # AC-1, AC-3


def test_rf26_correccion_por_el_residente(condo):
    folio = folio_de(condo.reportar(subtipo="Jardín o exterior"))  # Menor
    g = condo.get("inquilino", f"/reports/{folio}")
    d = condo.patch("inquilino", f"/reports/{folio}", {"subtipo": "Pasillo o área techada"}, g.headers["ETag"]).json()
    assert d["prioridadSugerida"] == "Normal"  # AC-5
    h = condo.get("admin", f"/reports/{folio}/history").json()["items"]
    assert any(x["tipo"] == "Correccion" and x.get("valorAnterior") == "Jardín o exterior" for x in h)  # AC-1, AC-2
    ajeno = folio_de(condo.reportar_en_unidad("residente_a301", unidad="A-301"))
    assert (
        condo.patch("inquilino", f"/reports/{ajeno}", {"descripcion": "Corrección no autorizada"}).status_code == 404
    )  # AC-4
    condo.asignar(folio)
    r = condo.patch("inquilino", f"/reports/{folio}", {"descripcion": "Otra descripción más larga"})
    assert r.status_code == 409 and mensaje(r) == "Transición no permitida"  # AC-3


# =============================================================== criterios adicionales
def test_rf17_ac2_ac3_ac4_independiente_union_y_aviso_de_cierre(condo):
    principal = folio_de(condo.reportar())
    dup = condo.reportar("residente_a301").json()
    assert dup["posibleDuplicado"] is True
    otro = folio_de(condo.reportar("residente_a301", descripcion="Otra lámpara fundida en la rampa"))
    assert (
        condo.cliente.delete(f"/api/v1/reports/{otro}/duplicate-flag", headers=condo.como("admin")).status_code == 204
    )
    assert condo.get("admin", f"/reports/{otro}").json()["posibleDuplicado"] is False  # AC-2
    u = condo.post("admin", f"/reports/{dup['folio']}/merges", json={"reportePrincipal": principal}).json()
    assert u["estado"] == "Unido" and u["reportePrincipal"] == principal  # AC-3
    condo.hasta_terminado(principal)
    condo.post("admin", f"/reports/{principal}/closures", json={})
    assert any("Cerrado" in m and dup["folio"] in m for m in bandeja(condo, "residente_a301"))  # AC-4


def test_rf20_ac1_ac2_monto_y_pagador(condo):
    folio = folio_de(condo.reportar_en_unidad())
    condo.post("admin", f"/reports/{folio}/costs", json={"monto": 1200, "pagador": "Condomino"})
    d = condo.get("admin", f"/reports/{folio}").json()
    assert (d["montoCosto"], d["pagador"]) == (1200, "Condomino")


def test_rf22_ac3_detenido_no_cuenta_y_ac4_umbral_configurable(condo):
    reloj.fijar(hora("21/09/2026 08:00"))
    detenido = folio_de(condo.reportar())  # Normal
    condo.asignar(detenido, prioridad="Normal")
    condo.iniciar(detenido)
    condo.post("conserje", f"/reports/{detenido}/holds", json={"motivo": "EsperaDePieza"})
    normal = folio_de(condo.reportar(descripcion="Otra luminaria fundida en la rampa"))  # Normal, sin asignar
    condo.put("admin", "/parameters/umbralEstancamientoNormalHoras", {"valor": 12})
    reloj.fijar(hora("21/09/2026 21:00"))  # 13 h después
    db = connect()
    assert notificaciones.revisar_estancados(db) == 1
    db.close()
    avisos = [a["reporte_folio"] for a in condo.sql("SELECT reporte_folio FROM aviso WHERE evento='Estancado'")]
    assert normal in avisos and detenido not in avisos


def test_rf23_ac2_el_pdf_lleva_las_mismas_cifras(condo):
    from reportlab import rl_config

    _urgente_con_tiempos(condo, "05/09/2026 08:00", 30, 22)
    pantalla = condo.get("admin", "/metrics", params={"desde": "2026-09-01", "hasta": "2026-09-30"}).json()
    u = next(p for p in pantalla["porPrioridad"] if p["prioridad"] == "Urgente")
    anterior, rl_config.pageCompression = rl_config.pageCompression, 0  # texto legible dentro del PDF
    try:
        pdf = condo.get(
            "admin",
            "/metrics",
            params={"desde": "2026-09-01", "hasta": "2026-09-30"},
            headers={"Accept": "application/pdf"},
        ).content
    finally:
        rl_config.pageCompression = anterior
    assert f"{u['resolucionPromedioHoras']:g} h".encode() in pdf and b"22 h" in pdf


# =============================================================== RNF-11: reintentos idempotentes
def test_rnf11_idempotency_key_no_duplica_el_reporte(condo):
    h = {"Idempotency-Key": "pwa-envio-000001"}
    datos = {
        "categoriaId": condo.cat("Iluminación"),
        "subtipo": "Pasillo o área techada",
        "descripcion": "Lámpara fundida en la rampa",
        "ubicacion": {"tipo": "AreaComun", "areaComunId": condo.id("rampa")},
        "esPeligroso": False,
    }
    a = condo.post(
        "inquilino",
        "/reports",
        headers=h,
        data={"datos": json.dumps(datos)},
        files=[("fotos", ("a.png", PNG, "image/png"))],
    )
    b = condo.post(
        "inquilino",
        "/reports",
        headers=h,
        data={"datos": json.dumps(datos)},
        files=[("fotos", ("a.png", PNG, "image/png"))],
    )
    assert a.status_code == b.status_code == 201 and a.json()["folio"] == b.json()["folio"]
    assert b.headers.get("Idempotent-Replayed") == "true" and b.headers["Location"] == a.headers["Location"]
    assert condo.get("admin", "/reports").json()["pagination"]["total"] == 1


def _datos_area(condo, descripcion, area="rampa"):
    return {
        "categoriaId": condo.cat("Otro"),
        "descripcion": descripcion,
        "ubicacion": {"tipo": "AreaComun", "areaComunId": condo.id(area)},
        "esPeligroso": False,
    }


def test_rnf11_un_error_no_se_guarda_y_se_puede_reintentar(condo):
    h = {"Idempotency-Key": "pwa-envio-000002"}
    malo = condo.post("inquilino", "/reports", headers=h, data={"datos": json.dumps(_datos_area(condo, "Fuga"))})
    assert malo.status_code == 422
    bueno = condo.post(
        "inquilino",
        "/reports",
        headers=h,
        data={"datos": json.dumps(_datos_area(condo, "Fuga de agua en la rampa del estacionamiento"))},
    )
    assert bueno.status_code == 201


def test_rnf11_la_clave_es_por_usuario(condo):
    h = {"Idempotency-Key": "misma-clave-0001"}
    datos = {"datos": json.dumps(_datos_area(condo, "Banca rota junto a la alberca", "alberca"))}
    f1 = condo.post("inquilino", "/reports", headers=h, data=datos).json()["folio"]
    f2 = condo.post("residente_a301", "/reports", headers=h, data=datos).json()["folio"]
    assert f1 != f2
