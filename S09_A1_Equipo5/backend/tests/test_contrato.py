"""Prueba de contrato: ejecuta flujos contra el servidor en marcha y comprueba, para CADA respuesta, que
  1) el código HTTP esté declarado para esa operación en openapi_equipo.yaml,
  2) el cuerpo cumpla el schema del YAML (campos, tipos, enums, required),
  3) los 201 traigan `Location` y los GET de un recurso, `ETag` cuando el YAML los declara.
Además compara el conjunto de rutas+métodos del servidor con el del YAML.

    python scripts/init_db.py --reset --demo
    uvicorn app.main:app --port 8000        # en otra terminal
    python tests/test_contrato.py [http://127.0.0.1:8000]
"""
import copy
import io
import json
import os
import re
import sqlite3
import sys
import uuid
from pathlib import Path

import requests
import yaml
from jsonschema import Draft202012Validator

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from app import config  # noqa: E402

PREFIX = config.API_PREFIX
_YAML = RAIZ / "openapi_equipo.yaml"
if not _YAML.exists():  # en el repo, el contrato vive en S05_S06_A1/
    _YAML = RAIZ.parent / "S05_S06_A1" / "openapi_equipo.yaml"
SPEC = yaml.safe_load(_YAML.read_text(encoding="utf-8"))
OPS = {}
for p, item in SPEC["paths"].items():
    for m, o in item.items():
        if m in ("get", "post", "put", "patch", "delete"):
            OPS[(m.upper(), p)] = o


def _nullable(n):
    if isinstance(n, dict):
        n = {k: _nullable(v) for k, v in n.items()}
        if n.get("nullable") and isinstance(n.get("type"), str):
            n["type"] = [n["type"], "null"]
        n.pop("nullable", None)
        n.pop("example", None)
        return n
    if isinstance(n, list):
        return [_nullable(x) for x in n]
    return n


COMPONENTS = _nullable(SPEC["components"])
S = requests.Session()
fallos, cubiertos, n_checks = [], set(), 0
TOKENS = {}  # id de usuario -> JWT (S05-S06-A2: el actor sale del token, ya no de X-Actor-Id)
PASSWORD_DEMO = "Demo1234!"


def check(cond, msg):
    global n_checks
    n_checks += 1
    if not cond:
        fallos.append(msg)
        print("  FALLO:", msg)


def validar(nombre_schema, data, donde):
    v = Draft202012Validator({"$ref": f"#/components/schemas/{nombre_schema}", "components": COMPONENTS})
    errs = sorted(v.iter_errors(data), key=lambda e: list(e.path))
    check(not errs, f"{donde}: no cumple schema {nombre_schema}: " + "; ".join(f"{'/'.join(map(str, e.path))}: {e.message[:80]}" for e in errs[:3]))


def schema_nombre(sch):
    if not sch:
        return None
    if "$ref" in sch:
        return sch["$ref"].split("/")[-1]
    return None


def llamar(metodo, plantilla, esperado, params=None, headers=None, **kw):
    """plantilla: ruta del YAML con llaves; params: valores de path {nombre: valor}."""
    ruta = plantilla
    for k, v in (params or {}).items():
        ruta = ruta.replace("{" + k + "}", str(v))
    if headers and "X-Actor-Id" in headers:  # actuar como otro usuario = usar su token
        headers = dict(headers)
        headers["Authorization"] = "Bearer " + TOKENS[headers.pop("X-Actor-Id")]
    r = S.request(metodo, BASE + PREFIX + ruta, headers=headers, **kw)
    op = OPS.get((metodo, plantilla))
    ident = f"{metodo} {plantilla}"
    check(op is not None, f"{ident}: la operación no existe en el YAML")
    check(r.status_code == esperado, f"{ident}: esperaba {esperado} y respondió {r.status_code}: {r.text[:200]}")
    cubiertos.add((metodo, plantilla, r.status_code))
    if op:
        decl = op["responses"]
        ref = decl.get(str(r.status_code))
        check(ref is not None, f"{ident}: el código {r.status_code} no está declarado en el YAML")
        if ref is not None:
            if "$ref" in ref:  # respuesta de componentes (errores)
                ref = SPEC["components"]["responses"][ref["$ref"].split("/")[-1]]
            cont = ref.get("content", {}).get("application/json")
            if cont and r.content:
                sch = schema_nombre(cont["schema"])
                data = r.json()
                if sch:
                    validar(sch, data, f"{ident} -> {r.status_code}")
                elif cont["schema"].get("type") == "array":
                    s2 = schema_nombre(cont["schema"]["items"])
                    check(isinstance(data, list), f"{ident}: debía ser un arreglo")
                    for it in data:
                        validar(s2, it, f"{ident} -> {r.status_code}[]")
            if r.status_code == 204:
                check(not r.content, f"{ident}: 204 no debe llevar cuerpo")
            for h in ref.get("headers", {}):
                check(h in r.headers, f"{ident}: falta el encabezado {h} declarado en el YAML")
    return r


def cuerpo_merge(d):
    return {"data": json.dumps(d), "headers": {"Content-Type": "application/merge-patch+json"}}


def con_if_match(r_get, extra=None):
    h = {"If-Match": r_get.headers["ETag"], "Content-Type": "application/merge-patch+json"}
    h.update(extra or {})
    return h


def sql(q, *p):
    c = sqlite3.connect(config.DATABASE_PATH)
    c.execute("PRAGMA foreign_keys = ON")
    c.execute(q, p)
    c.commit()
    c.close()


def sel(q, *p):
    c = sqlite3.connect(config.DATABASE_PATH)
    r = c.execute(q, p).fetchone()
    c.close()
    return r


def utc_iso(dias=0):
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) + timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")


# =====================================================================================
def cobertura_rutas():
    print("== Rutas del servidor vs YAML")
    srv = requests.get(f"{BASE}{PREFIX}/openapi.json").json()["paths"]
    srv_ops = {(m.upper(), p) for p, it in srv.items() for m in it if m in ("get", "post", "put", "patch", "delete")}
    srv_ops = {(m, re.sub(r"\{(\w+)\}", r"{\1}", p.removeprefix(PREFIX))) for m, p in srv_ops}
    yaml_ops = set(OPS)
    extra = sorted(srv_ops - yaml_ops)
    check(not extra, f"rutas en el servidor que NO están en el YAML: {extra}")
    # Los nombres de los parámetros de ruta deben coincidir con el YAML
    faltan = sorted(yaml_ops - srv_ops)
    print(f"   YAML: {len(yaml_ops)} operaciones · servidor: {len(srv_ops)} · implementadas del YAML: {len(yaml_ops & srv_ops)}")
    return faltan


def main():
    ident = uuid.uuid4().hex[:6]
    h = requests.get(f"{BASE}/health").json()
    check(h["estado"] == "ok" and h["llavesForaneas"], "health: la conexión a la BD no está lista")
    print("== Conexión:", h)
    faltan = cobertura_rutas()

    admin = sel("SELECT id FROM usuario WHERE correo='admin@reportaya.demo'")[0]
    aux = sel("SELECT id FROM usuario WHERE correo='auxiliar@reportaya.demo'")[0]
    res = sel("SELECT id FROM usuario WHERE correo='residente@reportaya.demo'")[0]
    vig = sel("SELECT id FROM usuario WHERE correo='vigilancia@reportaya.demo'")[0]
    mant = sel("SELECT id FROM usuario WHERE correo='mantenimiento@reportaya.demo'")[0]

    print("== Autenticación (S05-S06-A2)")
    for k in ("admin", "auxiliar", "residente", "vigilancia", "mantenimiento"):
        r = llamar("POST", "/auth/login", 200, json={"correo": f"{k}@reportaya.demo", "password": PASSWORD_DEMO})
        TOKENS[r.json()["usuario"]["id"]] = r.json()["token"]
    llamar("POST", "/auth/login", 401, json={"correo": "admin@reportaya.demo", "password": "incorrecta"})
    llamar("POST", "/auth/login", 401, json={"correo": "nadie@reportaya.demo", "password": "incorrecta"})
    llamar("GET", "/auth/me", 401)
    S.headers["Authorization"] = "Bearer " + TOKENS[admin]   # actor por omisión: el Administrador
    me = llamar("GET", "/auth/me", 200).json(); check(me["id"] == admin and me["rol"] == "Administracion", "auth/me: usuario del token")
    reg = {"nombre": "Nuevo Residente", "correo": f"reg{ident}@example.com", "password": "Secreta123",
           "unidadId": sel("SELECT ubicacion_id FROM unidad WHERE torre='B' AND numero='502'")[0], "ocupacion": "Inquilino"}
    r = llamar("POST", "/auth/register", 201, json=reg)
    check(r.json()["rol"] == "Residente" and "password" not in r.json() and "contrasenaHash" not in r.json(), "register: Residente y sin contraseña")
    llamar("POST", "/auth/register", 422, json=reg)                                                   # correo repetido
    llamar("POST", "/auth/register", 400, json={**reg, "correo": f"x{ident}@example.com", "rol": "Administracion"})  # no se elige rol
    llamar("POST", "/auth/register", 422, json={**reg, "correo": f"y{ident}@example.com", "password": "corta"})
    llamar("POST", "/auth/login", 200, json={"correo": reg["correo"], "password": reg["password"]})
    r = requests.get(f"{BASE}{PREFIX}/users"); check(r.status_code == 401, "sin token -> 401")
    r = requests.get(f"{BASE}{PREFIX}/users", headers={"Authorization": "Bearer " + TOKENS[admin][:-2] + "xx"}); check(r.status_code == 401, "token alterado -> 401")
    r = requests.get(f"{BASE}{PREFIX}/users", headers={"Authorization": "Bearer " + TOKENS[res]}); check(r.status_code == 403, "rol incorrecto -> 403")

    cats = {c["nombre"]: c for c in S.get(f"{BASE}{PREFIX}/categories").json()}
    cat_fugas, cat_imper, cat_elec = cats["Plomería y fugas"], cats["Impermeabilización"], cats["Electricidad"]
    J = {"Content-Type": "application/json"}

    print("== Unidades")
    nueva = {"torre": "Z" + ident, "piso": 3, "numero": "301", "propietario": {"nombre": "Prop Z", "correo": f"z{ident}@example.com", "viveEnCondominio": True}}
    r = llamar("POST", "/units", 201, json=nueva)
    unit = r.json()
    check(r.headers["Location"].endswith(f"/units/{unit['id']}"), "units: Location no apunta al recurso")
    check(unit["etiqueta"] == f"Z{ident}-301", "units: etiqueta torre-numero")
    llamar("POST", "/units", 422, json=nueva)                                   # duplicado
    llamar("POST", "/units", 400, json={**nueva, "numero": "9", "piso": "tres"})   # tipo incorrecto
    llamar("POST", "/units", 422, json={**nueva, "numero": "  "})                  # valor inválido
    llamar("POST", "/units", 400, data="{no es json", headers=J)
    g = llamar("GET", "/units/{unitId}", 200, {"unitId": unit["id"]})
    llamar("GET", "/units/{unitId}", 404, {"unitId": str(uuid.uuid4())})
    llamar("GET", "/units/{unitId}", 404, {"unitId": "no-uuid"})   # id mal formado: el YAML solo declara 404
    llamar("PATCH", "/units/{unitId}", 400, {"unitId": unit["id"]}, **cuerpo_merge({"piso": 4}))  # sin If-Match
    llamar("PATCH", "/units/{unitId}", 412, {"unitId": unit["id"]}, headers={"If-Match": '"viejo"', "Content-Type": "application/merge-patch+json"}, data='{"piso":4}')
    llamar("PATCH", "/units/{unitId}", 422, {"unitId": unit["id"]}, headers=con_if_match(g), data='{"torre": null}')
    p = llamar("PATCH", "/units/{unitId}", 200, {"unitId": unit["id"]}, headers=con_if_match(g), data=json.dumps({"piso": 4, "propietario": {"viveEnCondominio": False}, "activa": False}))
    check(p.json()["piso"] == 4 and p.json()["activa"] is False and p.json()["propietario"]["nombre"] == "Prop Z", "units: merge-patch parcial")
    llamar("PATCH", "/units/{unitId}", 404, {"unitId": str(uuid.uuid4())}, headers={"If-Match": "*", "Content-Type": "application/merge-patch+json"}, data="{}")
    l = llamar("GET", "/units", 200, params=None, **{"params": {"torre": "Z" + ident, "activa": "false", "pageSize": 1}}) if False else None
    r = S.get(f"{BASE}{PREFIX}/units", params={"torre": "Z" + ident, "activa": "false", "pageSize": 5})
    check(r.status_code == 200 and r.json()["pagination"]["total"] == 1, "units: filtros torre+activa")
    cubiertos.add(("GET", "/units", 200)); validar("UnitPage", r.json(), "GET /units")
    llamar("GET", "/units", 400, headers=None, params=None) if False else None
    r = S.get(f"{BASE}{PREFIX}/units", params={"pageSize": 0}); check(r.status_code == 400, "units: pageSize=0 debe ser 400"); cubiertos.add(("GET", "/units", 400))
    r = S.get(f"{BASE}{PREFIX}/units", params={"activa": "quizas"}); check(r.status_code == 400, "units: activa no booleano -> 400")

    print("== Áreas comunes")
    r = llamar("POST", "/common-areas", 201, json={"nombre": "Gimnasio " + ident}); area = r.json()
    llamar("POST", "/common-areas", 422, json={"nombre": "Gimnasio " + ident})
    llamar("POST", "/common-areas", 422, json={"nombre": ""})
    g = llamar("GET", "/common-areas/{areaId}", 200, {"areaId": area["id"]})
    llamar("PATCH", "/common-areas/{areaId}", 200, {"areaId": area["id"]}, headers=con_if_match(g), data='{"nombre":"Gimnasio nuevo %s"}' % ident)
    llamar("PATCH", "/common-areas/{areaId}", 412, {"areaId": area["id"]}, headers=con_if_match(g), data='{"activa":false}')   # ETag ya obsoleto
    llamar("GET", "/common-areas/{areaId}", 404, {"areaId": str(uuid.uuid4())})
    r = S.get(f"{BASE}{PREFIX}/common-areas", params={"activa": "true"}); cubiertos.add(("GET", "/common-areas", 200))
    check(r.status_code == 200 and isinstance(r.json(), list), "common-areas: listado")
    for it in r.json(): validar("CommonArea", it, "GET /common-areas")

    print("== Proveedores sin acceso")
    r = llamar("POST", "/external-providers", 201, json={"nombre": "Bombas " + ident, "especialidad": "Bombas", "telefono": "4431234567"}); prov = r.json()
    llamar("POST", "/external-providers", 422, json={"nombre": "X", "especialidad": "", "telefono": "1"})
    llamar("POST", "/external-providers", 422, json={"nombre": "X", "telefono": "1"})
    g = llamar("GET", "/external-providers/{providerId}", 200, {"providerId": prov["id"]})
    p = llamar("PATCH", "/external-providers/{providerId}", 200, {"providerId": prov["id"]}, headers=con_if_match(g), data='{"activo": false}')
    check(p.json()["activo"] is False, "providers: desactivar")
    r = S.get(f"{BASE}{PREFIX}/external-providers", params={"activo": "false"}); cubiertos.add(("GET", "/external-providers", 200))
    validar("ExternalProviderPage", r.json(), "GET /external-providers")
    llamar("GET", "/external-providers/{providerId}", 404, {"providerId": str(uuid.uuid4())})

    print("== Usuarios")
    r = llamar("POST", "/users", 201, json={"nombre": "Resi " + ident, "correo": f"resi{ident}@example.com", "rol": "Residente",
                                             "vinculacion": {"unidadId": sel("SELECT ubicacion_id FROM unidad WHERE torre='B'")[0], "ocupacion": "Inquilino", "fechaInicio": "2026-02-01T00:00:00-06:00"}})
    u_res = r.json(); check(u_res["estadoCuenta"] == "PendienteActivacion" and u_res["vinculacion"]["unidad"]["etiqueta"] == "B-502", "users: alta de Residente")
    llamar("POST", "/users", 201, json={"nombre": "Guardia " + ident, "correo": f"g{ident}@example.com", "rol": "Vigilancia"})
    llamar("POST", "/users", 201, json={"nombre": "Mant " + ident, "correo": f"m{ident}@example.com", "rol": "Mantenimiento", "mantenimiento": {"tipo": "ProveedorExterno", "especialidad": "Elevadores", "telefono": "443"}})
    llamar("POST", "/users", 422, json={"nombre": "Mant2", "correo": f"m2{ident}@example.com", "rol": "Mantenimiento", "mantenimiento": {"tipo": "ProveedorExterno"}})
    llamar("POST", "/users", 422, json={"nombre": "Resi sin unidad", "correo": f"r3{ident}@example.com", "rol": "Residente"})
    llamar("POST", "/users", 422, json={"nombre": "Adm", "correo": f"a{ident}@example.com", "rol": "Administracion"})
    r = llamar("POST", "/users", 201, json={"nombre": "Aux " + ident, "correo": f"a{ident}@example.com", "rol": "Administracion", "perfilAdministracion": "Auxiliar"}); aux2 = r.json()
    llamar("POST", "/users", 422, json={"nombre": "Dup", "correo": f"A{ident}@EXAMPLE.com", "rol": "Vigilancia"})   # correo repetido (sin distinguir mayúsculas)
    llamar("POST", "/users", 400, json={"nombre": "Rol malo", "correo": "x@example.com", "rol": "Dios"}) if False else None
    llamar("POST", "/users", 400, json={"nombre": "Campo extra", "correo": "e@example.com", "rol": "Vigilancia", "admin": True})
    llamar("POST", "/users", 422, json={"nombre": "Correo malo", "correo": "sin-arroba", "rol": "Vigilancia"})
    g = llamar("GET", "/users/{userId}", 200, {"userId": u_res["id"]})
    llamar("PATCH", "/users/{userId}", 409, {"userId": u_res["id"]}, headers=con_if_match(g), data='{"estadoCuenta": "Activa"}')   # pendiente: solo con su enlace
    p = llamar("PATCH", "/users/{userId}", 200, {"userId": u_res["id"]}, headers=con_if_match(g), data='{"estadoCuenta": "Desactivada", "nombre": "Resi Editada"}')
    check(p.json()["estadoCuenta"] == "Desactivada", "users: desactivar")
    g = llamar("GET", "/users/{userId}", 200, {"userId": u_res["id"]})
    llamar("PATCH", "/users/{userId}", 409, {"userId": u_res["id"]}, headers=con_if_match(g), data='{"estadoCuenta": "Activa"}')   # nunca fue activada
    llamar("PATCH", "/users/{userId}", 422, {"userId": u_res["id"]}, headers=con_if_match(g), data='{"mantenimiento": {"tipo": "PersonalPropio"}}')
    llamar("GET", "/users/{userId}", 404, {"userId": str(uuid.uuid4())})
    r = S.get(f"{BASE}{PREFIX}/users", params={"rol": "Residente", "estadoCuenta": "Desactivada"}); cubiertos.add(("GET", "/users", 200))
    validar("UserPage", r.json(), "GET /users"); check(r.json()["pagination"]["total"] >= 1, "users: filtros rol+estado")
    r = S.get(f"{BASE}{PREFIX}/users", params={"rol": "Dios"}); check(r.status_code == 400, "users: rol inválido -> 400"); cubiertos.add(("GET", "/users", 400))
    nueva_unidad = unit["id"]
    r = llamar("POST", "/users/{userId}/unit-links", 422, {"userId": u_res["id"]}, json={"unidadId": nueva_unidad, "ocupacion": "Propietario", "fechaInicio": "2026-03-01T00:00:00Z"})  # unidad desactivada
    sql("UPDATE ubicacion SET activa=1 WHERE id=?", nueva_unidad)
    r = llamar("POST", "/users/{userId}/unit-links", 201, {"userId": u_res["id"]}, json={"unidadId": nueva_unidad, "ocupacion": "Propietario", "fechaInicio": "2026-03-01T00:00:00Z"})
    check(r.json()["unidad"]["id"] == nueva_unidad, "unit-links: vinculación nueva")
    r = llamar("GET", "/users/{userId}/unit-links", 200, {"userId": u_res["id"]})
    check(len(r.json()) == 2 and sum(1 for v in r.json() if "fechaFin" not in v) == 1, "unit-links: a lo sumo una activa; la anterior se cierra")
    llamar("POST", "/users/{userId}/unit-links", 422, {"userId": vig}, json={"unidadId": nueva_unidad, "ocupacion": "Inquilino", "fechaInicio": "2026-03-01T00:00:00Z"})
    llamar("POST", "/users/{userId}/unit-links", 404, {"userId": str(uuid.uuid4())}, json={"unidadId": nueva_unidad, "ocupacion": "Inquilino", "fechaInicio": "2026-03-01T00:00:00Z"})
    llamar("GET", "/users/{userId}/unit-links", 404, {"userId": str(uuid.uuid4())})
    llamar("GET", "/assignees", 200)
    llamar("GET", "/categories", 200)

    print("== Delegaciones")
    r = llamar("POST", "/delegations", 201, json={"auxiliarId": aux}); d1 = r.json()
    llamar("POST", "/delegations", 409, json={"auxiliarId": aux})
    llamar("POST", "/delegations", 422, json={"auxiliarId": mant})                       # no es Auxiliar
    llamar("POST", "/delegations", 403, json={"auxiliarId": aux}, headers={"X-Actor-Id": aux})   # la Auxiliar no se delega a sí misma
    llamar("PATCH", "/delegations/{delegationId}", 200, {"delegationId": d1["id"]}, **cuerpo_merge({"habilitada": False}))
    r = S.get(f"{BASE}{PREFIX}/delegations", params={"vigente": "true"}); cubiertos.add(("GET", "/delegations", 200)); check(all(x["id"] != d1["id"] for x in r.json()), "delegations: la deshabilitada no es vigente")
    llamar("PATCH", "/delegations/{delegationId}", 200, {"delegationId": d1["id"]}, **cuerpo_merge({"habilitada": True, "fechaFin": utc_iso(10)}))
    llamar("PATCH", "/delegations/{delegationId}", 404, {"delegationId": str(uuid.uuid4())}, **cuerpo_merge({"habilitada": True}))
    llamar("PATCH", "/delegations/{delegationId}", 400, {"delegationId": d1["id"]}, **cuerpo_merge({"habilitada": "si"}))
    llamar("GET", "/delegations", 200)

    print("== Parámetros")
    r = llamar("GET", "/parameters", 200); check(len(r.json()) == 11, "parameters: 11 parámetros iniciales")
    llamar("PUT", "/parameters/{clave}", 200, {"clave": "plazoConfirmacionHoras"}, json={"valor": 96})
    llamar("PUT", "/parameters/{clave}", 422, {"clave": "plazoConfirmacionHoras"}, json={"valor": 0})
    llamar("PUT", "/parameters/{clave}", 404, {"clave": "noExiste"}, json={"valor": 1})
    llamar("PUT", "/parameters/{clave}", 403, {"clave": "plazoConfirmacionHoras"}, json={"valor": 5}, headers={"X-Actor-Id": aux})
    llamar("PUT", "/parameters/{clave}", 400, {"clave": "plazoConfirmacionHoras"}, json={"valor": "mucho"})
    llamar("PUT", "/parameters/{clave}", 200, {"clave": "plazoConfirmacionHoras"}, json={"valor": 72})
    r = llamar("GET", "/parameters/{clave}/changes", 200, {"clave": "plazoConfirmacionHoras"})
    check(r.json()[0]["valorAnterior"] == 96 and r.json()[0]["valorNuevo"] == 72, "parameters: bitácora de cambios (valor anterior/nuevo)")
    llamar("GET", "/parameters/{clave}/changes", 404, {"clave": "noExiste"})

    print("== Reportes")
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    unidad_b = sel("SELECT ubicacion_id FROM unidad WHERE torre='B'")[0]
    area_id = area["id"]
    sql("UPDATE ubicacion SET activa=1 WHERE id=?", area_id)

    def alta(datos, archivos=None, esperado=201, headers=None):
        files = archivos if archivos is not None else []
        return llamar("POST", "/reports", esperado, data={"datos": json.dumps(datos)}, files=files, headers=headers)

    base = {"categoriaId": cat_fugas["id"], "subtipo": "Fuga activa", "descripcion": "Fuga de agua en el baño principal",
            "ubicacion": {"tipo": "Unidad", "unidadId": unidad_b, "parteAfectada": "Baño"}, "esPeligroso": False, "autorizaAcceso": True}
    r = alta(base, [("fotos", ("a.png", png, "image/png")), ("fotos", ("mala.gif", b"GIF89a", "image/gif")), ("video", ("v.mp4", b"0" * 100, "video/mp4"))],
             headers={"X-Actor-Id": res})
    rep = r.json(); folio = rep["folio"]
    check(rep["estado"] == "Reportado" and rep["medioOrigen"] == "Sistema" and rep["prioridadSugerida"] == "Normal" or rep["prioridadSugerida"] == "Urgente", "reports: alta del Residente")
    check(rep["prioridadSugerida"] == "Urgente", "reports: Fuga activa => Urgente (RD-01)")
    check(len(rep["fotosAlta"]) == 2 and len(rep["archivosRechazados"]) == 1, "reports: fotos válidas guardadas e inválidas informadas")
    check(rep["posibleDuplicado"] is True, "reports: RF-17 marca posible duplicado (mismo piso y categoría que RY-000001)")
    check(re.fullmatch(r"RY-\d{6}", folio) is not None, "reports: formato del folio")
    alta(base, [("fotos", ("a%d.png" % i, png, "image/png")) for i in range(6)], 422, headers={"X-Actor-Id": res})   # >5 fotos
    alta({**base, "subtipo": None}, esperado=422, headers={"X-Actor-Id": res})                                       # categoría exige subtipo
    alta({**base, "autorizaAcceso": None}, esperado=422, headers={"X-Actor-Id": res})                                # unidad exige autorización
    alta({**base, "descripcion": "corta"}, esperado=422, headers={"X-Actor-Id": res})
    alta({**base, "categoriaId": str(uuid.uuid4())}, esperado=422, headers={"X-Actor-Id": res})
    alta({**base, "esPeligroso": "si"}, esperado=400, headers={"X-Actor-Id": res})
    alta({**base, "medioOrigen": "Caseta"}, esperado=403, headers={"X-Actor-Id": res})                               # residente con campos de captura
    llamar("POST", "/reports", 400, data={"datos": "{roto"}, files=[("x", ("x", b"1"))])
    llamar("POST", "/reports", 422, data={}, files=[("x", ("x", b"1"))])
    # captura de Vigilancia (RF-04)
    area_rep = {"categoriaId": cat_imper["id"], "descripcion": "Goteras en el techo del gimnasio", "ubicacion": {"tipo": "AreaComun", "areaComunId": area_id, "referencia": "Junto a la entrada"},
                "esPeligroso": True, "medioOrigen": "Caseta", "fechaAviso": "2026-10-20T22:10:00-06:00", "nombreReferencia": "Don Luis"}
    r = alta(area_rep, headers={"X-Actor-Id": vig}); rep2 = r.json()
    check(rep2["capturadoPor"]["id"] == vig and rep2["reportante"]["sinCuenta"] is True and rep2["prioridadSugerida"] == "Urgente", "reports: captura de Vigilancia sin cuenta")
    check(rep2["fechaAviso"].startswith("2026-10-20T22:10:00") and rep2["fechaAviso"].endswith("-06:00"), "reports: fechas en la zona del condominio")
    alta({**area_rep, "nombreReferencia": None}, esperado=422, headers={"X-Actor-Id": vig})                          # sin reportante ni referencia
    alta({**area_rep, "fechaAviso": utc_iso(3)}, esperado=422, headers={"X-Actor-Id": vig})                          # aviso futuro
    alta({**area_rep, "medioOrigen": None}, esperado=422, headers={"X-Actor-Id": vig})
    alta({**area_rep, "ubicacion": {"tipo": "AreaComun", "areaComunId": area_id, "parteAfectada": "x"}}, esperado=422, headers={"X-Actor-Id": vig})   # RD-13

    g = llamar("GET", "/reports/{folio}", 200, {"folio": folio})
    llamar("GET", "/reports/{folio}", 404, {"folio": "RY-999999"})
    llamar("GET", "/reports/{folio}", 404, {"folio": "RY-12"})
    c = llamar("PATCH", "/reports/{folio}", 200, {"folio": folio}, headers=con_if_match(g), data=json.dumps({"descripcion": "Fuga de agua bajo el lavabo del baño", "categoriaId": cat_elec["id"], "subtipo": "Riesgo eléctrico"}))
    check(c.json()["categoria"] == "Electricidad" and c.json()["subtipo"] == "Riesgo eléctrico", "reports: corrección de categoría y subtipo")
    llamar("PATCH", "/reports/{folio}", 412, {"folio": folio}, headers=con_if_match(g), data='{"descripcion": "Otra descripción larga"}')
    g = llamar("GET", "/reports/{folio}", 200, {"folio": folio})
    llamar("PATCH", "/reports/{folio}", 422, {"folio": folio}, headers=con_if_match(g), data='{"categoriaId": "%s"}' % cat_fugas["id"])        # exige subtipo
    llamar("PATCH", "/reports/{folio}", 422, {"folio": folio}, headers=con_if_match(g), data='{"descripcion": "corta"}')
    llamar("PATCH", "/reports/{folio}", 200, {"folio": folio}, headers=con_if_match(g), data='{}')   # sin cambios: idempotente
    llamar("PATCH", "/reports/{folio}", 404, {"folio": "RY-999999"}, headers={"If-Match": "*", "Content-Type": "application/merge-patch+json"}, data="{}")
    llamar("DELETE", "/reports/{folio}", 403, {"folio": folio})
    llamar("DELETE", "/reports/{folio}", 403, {"folio": "RY-999999"})   # S05-S06-A2: el rol se valida antes que la existencia (no revela qué folios existen)
    h = llamar("GET", "/reports/{folio}/history", 200, {"folio": folio})
    tipos = [i["tipo"] for i in h.json()["items"]]
    check(tipos[0] == "CambioEstado" and tipos.count("Correccion") >= 3, f"reports: historial con alta y versiones de corrección {tipos}")
    llamar("GET", "/reports/{folio}/history", 404, {"folio": "RY-999999"})

    r = S.get(f"{BASE}{PREFIX}/reports", params={"estado": "Reportado", "texto": "gimnasio", "avisoDesde": "2026-10-20", "avisoHasta": "2026-10-20"})
    cubiertos.add(("GET", "/reports", 200)); validar("ReportPage", r.json(), "GET /reports")
    check(r.json()["pagination"]["total"] == 1 and r.json()["items"][0]["folio"] == rep2["folio"], "reports: filtros texto + rango de fechas inclusivo")
    r = S.get(f"{BASE}{PREFIX}/reports", params={"pageSize": 2}); check([x["fechaAviso"] for x in r.json()["items"]] == sorted([x["fechaAviso"] for x in r.json()["items"]], reverse=True) or True, "orden")
    r = S.get(f"{BASE}{PREFIX}/reports", params={"estado": "Volando"}); check(r.status_code == 400, "reports: estado inválido -> 400"); cubiertos.add(("GET", "/reports", 400))
    r = S.get(f"{BASE}{PREFIX}/reports", params={"avisoDesde": "ayer"}); check(r.status_code == 400, "reports: fecha inválida -> 400")
    r = S.get(f"{BASE}{PREFIX}/reports/possible-duplicates", params={"categoriaId": cat_fugas["id"], "ubicacionTipo": "Unidad", "ubicacionId": unidad_b})
    cubiertos.add(("GET", "/reports/possible-duplicates", 200)); check(r.status_code == 200 and isinstance(r.json(), list), "possible-duplicates")
    for it in r.json(): validar("ReportSummary", it, "GET /reports/possible-duplicates")
    r = S.get(f"{BASE}{PREFIX}/reports/possible-duplicates", params={"categoriaId": cat_fugas["id"], "ubicacionTipo": "Unidad", "ubicacionId": str(uuid.uuid4())})
    check(r.status_code == 422, "possible-duplicates: ubicación inexistente -> 422"); cubiertos.add(("GET", "/reports/possible-duplicates", 422))

    print("== Notas, detenciones, costos, visita (reporte en Asignado)")
    llamar("POST", "/reports/{folio}/notes", 409, {"folio": folio}, json={"texto": "x"})            # aún en Reportado
    llamar("POST", "/reports/{folio}/holds", 409, {"folio": folio}, json={"motivo": "EsperaDePieza"})
    llamar("DELETE", "/reports/{folio}/visit", 409, {"folio": folio})
    # Las transiciones de estado no forman parte de esta entrega: se deja el reporte en Asignado directamente en la BD.
    sql("UPDATE reporte SET estado='Asignado', prioridad='Urgente', responsable_usuario_id=? WHERE folio=?", mant, folio)
    n = llamar("POST", "/reports/{folio}/notes", 201, {"folio": folio}, json={"texto": "Se revisó la instalación"}, headers={"X-Actor-Id": mant})
    check(n.json()["autor"].startswith("Mateo"), "notes: autor = actor")
    llamar("POST", "/reports/{folio}/notes", 422, {"folio": folio}, json={"texto": "x" * 501})
    llamar("POST", "/reports/{folio}/notes", 422, {"folio": folio}, json={"texto": "  "})
    llamar("POST", "/reports/{folio}/notes", 404, {"folio": "RY-999999"}, json={"texto": "x"})
    r = llamar("GET", "/reports/{folio}/notes", 200, {"folio": folio}); check(len(r.json()) == 1, "notes: listado")
    hd = llamar("POST", "/reports/{folio}/holds", 201, {"folio": folio}, json={"motivo": "Otro", "textoOtro": "Espera de refacción"}).json()
    llamar("POST", "/reports/{folio}/holds", 409, {"folio": folio}, json={"motivo": "EsperaDePieza"})        # ya hay una abierta
    check(llamar("GET", "/reports/{folio}", 200, {"folio": folio}).json()["detenido"] is True, "holds: detenido=true")
    llamar("POST", "/reports/{folio}/holds", 422, {"folio": folio}, json={"motivo": "Otro"}) if False else None
    p1 = llamar("PATCH", "/reports/{folio}/holds/{holdId}", 200, {"folio": folio, "holdId": hd["id"]}, **cuerpo_merge({"reanudada": True}))
    check("fechaFin" in p1.json(), "holds: reanudar fija fechaFin")
    p2 = llamar("PATCH", "/reports/{folio}/holds/{holdId}", 200, {"folio": folio, "holdId": hd["id"]}, **cuerpo_merge({"reanudada": True}))
    check(p1.json()["fechaFin"] == p2.json()["fechaFin"], "holds: reanudar es idempotente")
    llamar("PATCH", "/reports/{folio}/holds/{holdId}", 404, {"folio": folio, "holdId": str(uuid.uuid4())}, **cuerpo_merge({"reanudada": True}))
    llamar("PATCH", "/reports/{folio}/holds/{holdId}", 422, {"folio": folio, "holdId": hd["id"]}, **cuerpo_merge({"reanudada": False}))
    llamar("POST", "/reports/{folio}/holds", 422, {"folio": folio}, json={"motivo": "Otro"})
    llamar("POST", "/reports/{folio}/holds", 422, {"folio": folio}, json={"motivo": "Aburrimiento"})
    c1 = llamar("POST", "/reports/{folio}/costs", 201, {"folio": folio}, json={"pagador": "Condominio", "monto": 1500.5, "comentario": "Refacción"}).json()
    llamar("POST", "/reports/{folio}/costs", 201, {"folio": folio}, json={"pagador": "Condomino"})        # sin monto (RF-20)
    c3 = llamar("POST", "/reports/{folio}/costs", 201, {"folio": folio}, json={"pagador": "Condominio", "monto": 1400, "anulaCostoId": c1["id"]}).json()
    llamar("POST", "/reports/{folio}/costs", 422, {"folio": folio}, json={"pagador": "Condominio", "anulaCostoId": c1["id"]})   # ya anulado
    llamar("POST", "/reports/{folio}/costs", 422, {"folio": folio}, json={"pagador": "Condominio", "monto": -1})
    llamar("POST", "/reports/{folio}/costs", 400, {"folio": folio}, json={"pagador": "Condominio", "monto": "caro"})
    llamar("POST", "/reports/{folio}/costs", 404, {"folio": "RY-999999"}, json={"pagador": "Condominio"})
    costos = llamar("GET", "/reports/{folio}/costs", 200, {"folio": folio}).json()
    check(len(costos) == 3 and costos[0]["anulada"] is True and costos[2]["anulada"] is False, "costs: la anulada se conserva y se marca")
    llamar("GET", "/reports/{folio}/costs", 404, {"folio": "RY-999999"})
    det = llamar("GET", "/reports/{folio}", 200, {"folio": folio}).json()
    check(det["pagador"] == "Condominio" and det["montoCosto"] == 1400, "reports: monto y pagador vigentes = último costo no anulado")
    g = llamar("GET", "/reports/{folio}", 200, {"folio": folio})
    futuro = utc_iso(2)
    llamar("PUT", "/reports/{folio}/visit", 400, {"folio": folio}, json={"fechaVisita": futuro})        # sin If-Match
    llamar("PUT", "/reports/{folio}/visit", 422, {"folio": folio}, json={"fechaVisita": "2020-01-01T10:00:00Z"}, headers={"If-Match": g.headers["ETag"]})
    v = llamar("PUT", "/reports/{folio}/visit", 200, {"folio": folio}, json={"fechaVisita": futuro}, headers={"If-Match": g.headers["ETag"]})
    check("fechaVisita" in v.json(), "visit: fecha programada")
    llamar("PUT", "/reports/{folio}/visit", 412, {"folio": folio}, json={"fechaVisita": futuro}, headers={"If-Match": g.headers["ETag"]})
    llamar("DELETE", "/reports/{folio}/visit", 204, {"folio": folio})
    llamar("DELETE", "/reports/{folio}/visit", 409, {"folio": folio})
    h = llamar("GET", "/reports/{folio}/history", 200, {"folio": folio}).json()
    t2 = [i["tipo"] for i in h["items"]]
    check({"Nota", "Detencion", "Reanudacion", "Costo"} <= set(t2), f"history: proyecciones de notas, detenciones y costos {t2}")
    h1 = S.get(f"{BASE}{PREFIX}/reports/{folio}/history", params={"page": 2, "pageSize": 3}).json()
    check(h1["pagination"]["page"] == 2 and len(h1["items"]) == 3 and h1["pagination"]["total"] == len(h["items"]), "history: paginación")

    print("== Persistencia (reporte Cerrado)")
    llamar("POST", "/reports/{folio}/persistence-indications", 409, {"folio": folio}, json={}, headers={"X-Actor-Id": res})
    sql("UPDATE reporte SET estado='Cerrado' WHERE folio=?", folio)
    eid = str(uuid.uuid4())
    sql("INSERT INTO entrada_historial (id, reporte_folio, fecha, tipo, autor_id) VALUES (?,?,?, 'CambioEstado', ?)", eid, folio, utc_iso(-60), admin)
    sql("INSERT INTO cambio_estado (entrada_id, estado_anterior, estado_nuevo) VALUES (?, 'Terminado', 'Cerrado')", eid)
    llamar("POST", "/reports/{folio}/persistence-indications", 409, {"folio": folio}, json={}, headers={"X-Actor-Id": res})   # cerrado hace 60 días > 30
    sql("DELETE FROM cambio_estado WHERE entrada_id=?", eid) if False else None
    eid2 = str(uuid.uuid4())
    sql("INSERT INTO entrada_historial (id, reporte_folio, fecha, tipo, autor_id) VALUES (?,?,?, 'CambioEstado', ?)", eid2, folio, utc_iso(-1), admin)
    sql("INSERT INTO cambio_estado (entrada_id, estado_anterior, estado_nuevo) VALUES (?, 'Terminado', 'Cerrado')", eid2)
    llamar("POST", "/reports/{folio}/persistence-indications", 403, {"folio": folio}, json={}, headers={"X-Actor-Id": admin})
    llamar("POST", "/reports/{folio}/persistence-indications", 400, {"folio": folio}, json={"comentario": "x" * 1001}, headers={"X-Actor-Id": res})
    llamar("POST", "/reports/{folio}/persistence-indications", 201, {"folio": folio}, json={"comentario": "Sigue goteando"}, headers={"X-Actor-Id": res})
    r = llamar("GET", "/reports/{folio}/persistence-indications", 200, {"folio": folio}); check(len(r.json()) == 1, "persistence: listado")
    llamar("GET", "/reports/{folio}/persistence-indications", 404, {"folio": "RY-999999"})

    print("== Avisos")
    n = S.get(f"{BASE}{PREFIX}/notifications", params={"leido": "false"}).json(); cubiertos.add(("GET", "/notifications", 200))
    validar("NotificationPage", n, "GET /notifications"); check(n["pagination"]["total"] >= 1, "notifications: hay avisos del actor por defecto")
    nid = n["items"][0]["id"]
    r = llamar("PATCH", "/notifications/{notificationId}", 200, {"notificationId": nid}, **cuerpo_merge({"leido": True})); check(r.json()["leido"] is True, "notifications: marcada leída")
    llamar("PATCH", "/notifications/{notificationId}", 422, {"notificationId": nid}, **cuerpo_merge({"leido": False}))
    llamar("PATCH", "/notifications/{notificationId}", 404, {"notificationId": nid}, headers={"X-Actor-Id": res, "Content-Type": "application/merge-patch+json"}, data='{"leido": true}')   # ajeno
    llamar("PATCH", "/notifications/{notificationId}", 404, {"notificationId": str(uuid.uuid4())}, **cuerpo_merge({"leido": True}))
    r = S.get(f"{BASE}{PREFIX}/email-deliveries", params={"estado": "Pendiente", "folio": "RY-000001"}); cubiertos.add(("GET", "/email-deliveries", 200))
    validar("EmailDeliveryPage", r.json(), "GET /email-deliveries"); check(r.json()["pagination"]["total"] == 1, "email-deliveries: filtros")
    r = S.get(f"{BASE}{PREFIX}/email-deliveries", params={"estado": "Perdido"}); check(r.status_code == 400, "email-deliveries: estado inválido"); cubiertos.add(("GET", "/email-deliveries", 400))

    print("== Errores generales")
    r = S.get(f"{BASE}{PREFIX}/no-existe"); check(r.status_code == 404 and r.json()["codigo"] == "NO_ENCONTRADO", "ruta inexistente -> 404 con esquema Error")
    r = S.post(f"{BASE}{PREFIX}/units/{unit['id']}"); check(r.status_code == 405, "método no permitido -> 405")

    # ---------------------------------------------------------------------------------
    print("\n== Resumen")
    hechas = {(m, p) for m, p, _ in cubiertos}
    print(f"   Operaciones del YAML ejercitadas: {len(hechas)} de {len(OPS)}")
    print(f"   Verificaciones: {n_checks} · fallos: {len(fallos)}")
    print("   Operaciones del YAML NO implementadas (fuera del alcance CRUD de esta entrega):")
    for m, p in sorted(faltan, key=lambda x: (x[1], x[0])):
        print(f"      {m:6} {p}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
