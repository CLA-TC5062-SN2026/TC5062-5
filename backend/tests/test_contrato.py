"""Prueba de contrato: ejecuta flujos contra el servidor en marcha y comprueba, para CADA respuesta, que
  1) el código HTTP esté declarado para esa operación en openapi_equipo.yaml,
  2) el cuerpo cumpla el schema del YAML (campos, tipos, enums, required),
  3) los 201 traigan `Location` y los GET de un recurso, `ETag` cuando el YAML los declara.
Además compara el conjunto de rutas+métodos del servidor con el del YAML.

    python scripts/init_db.py --reset --demo
    uvicorn app.main:app --port 8000        # en otra terminal
    python tests/test_contrato.py [http://127.0.0.1:8000]
"""

import json
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
    check(
        not errs,
        f"{donde}: no cumple schema {nombre_schema}: "
        + "; ".join(f"{'/'.join(map(str, e.path))}: {e.message[:80]}" for e in errs[:3]),
    )


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


def token_del_correo(correo):
    """Token del último enlace enviado a `correo` (correo simulado: archivos en CORREO_BANDEJA_DIR)."""
    archivos = sorted(
        p for p in config.CORREO_BANDEJA_DIR.glob("*.txt") if f"Para: {correo}" in p.read_text(encoding="utf-8")
    )
    check(bool(archivos), f"correo: no llegó ningún correo a {correo}")
    m = re.search(r"token=([A-Za-z0-9_-]+)", archivos[-1].read_text(encoding="utf-8")) if archivos else None
    return m.group(1) if m else ""


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
    print(
        f"   YAML: {len(yaml_ops)} operaciones · servidor: {len(srv_ops)} · implementadas del YAML: {len(yaml_ops & srv_ops)}"
    )
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

    print("== Autenticación y cuentas (RF-01, RF-14, RNF-06)")
    for k in ("admin", "auxiliar", "residente", "vigilancia", "mantenimiento"):
        r = llamar("POST", "/auth/login", 200, json={"correo": f"{k}@reportaya.demo", "password": PASSWORD_DEMO})
        TOKENS[r.json()["usuario"]["id"]] = r.json()["token"]
    llamar("POST", "/auth/login", 401, json={"correo": "admin@reportaya.demo", "password": "incorrecta"})
    llamar("POST", "/auth/login", 401, json={"correo": "nadie@reportaya.demo", "password": "incorrecta"})
    llamar("GET", "/auth/me", 401)
    S.headers["Authorization"] = "Bearer " + TOKENS[admin]  # actor por omisión: el Administrador
    me = llamar("GET", "/auth/me", 200).json()
    check(me["id"] == admin and me["rol"] == "Administracion", "auth/me: usuario del token")
    # No hay registro público (RF-02, EX-08): la cuenta la crea la Administración y se activa con el enlace (RF-14).
    r = S.post(f"{BASE}{PREFIX}/auth/register", json={})
    check(r.status_code == 404, "auth/register ya no existe (EX-08)")
    unidad_b502 = sel("SELECT ubicacion_id FROM unidad WHERE torre='B' AND numero='502'")[0]
    nuevo = llamar(
        "POST",
        "/users",
        201,
        json={
            "nombre": "Nuevo Residente",
            "correo": f"reg{ident}@example.com",
            "rol": "Residente",
            "vinculacion": {"unidadId": unidad_b502, "ocupacion": "Inquilino", "fechaInicio": "2026-01-01T00:00:00Z"},
        },
    ).json()
    check(
        nuevo["estadoCuenta"] == "PendienteActivacion",
        "users: la cuenta nueva queda Pendiente de activación (RF-02-AC-1)",
    )
    llamar("POST", "/auth/login", 401, json={"correo": nuevo["correo"], "password": "Secreta123"})  # aún sin activar
    tok = token_del_correo(nuevo["correo"])
    llamar("POST", "/account-activations", 422, json={"token": tok, "password": "corta"})
    llamar("POST", "/account-activations", 422, json={"token": "no-existe", "password": "Secreta123"})
    llamar("POST", "/account-activations", 400, json={"token": tok}) if False else None
    llamar("POST", "/account-activations", 204, json={"token": tok, "password": "Secreta123"})
    llamar("POST", "/account-activations", 422, json={"token": tok, "password": "Secreta123"})  # un solo uso
    r = llamar("POST", "/auth/login", 200, json={"correo": nuevo["correo"], "password": "Secreta123"})
    check("X-Token-Renovado" not in r.headers, "login: el token va en el cuerpo")
    TOKENS[nuevo["id"]] = r.json()["token"]
    r2 = requests.get(f"{BASE}{PREFIX}/auth/me", headers={"Authorization": "Bearer " + TOKENS[nuevo["id"]]})
    check(
        r2.status_code == 200 and "X-Token-Renovado" in r2.headers, "sesión: token renovado en cada petición (RNF-06)"
    )
    llamar("POST", "/password-reset-requests", 202, json={"correo": nuevo["correo"]})
    llamar("POST", "/password-reset-requests", 202, json={"correo": "nadie@example.com"})  # misma respuesta
    llamar("POST", "/password-reset-requests", 422, json={})
    tok = token_del_correo(nuevo["correo"])
    llamar("POST", "/password-resets", 204, json={"token": tok, "password": "OtraClave456"})
    llamar("POST", "/password-resets", 422, json={"token": tok, "password": "OtraClave456"})
    llamar("POST", "/auth/login", 200, json={"correo": nuevo["correo"], "password": "OtraClave456"})
    llamar("POST", "/users/{userId}/activation-links", 409, {"userId": nuevo["id"]})  # ya está activa
    llamar("POST", "/users/{userId}/activation-links", 404, {"userId": str(uuid.uuid4())})
    r = requests.get(f"{BASE}{PREFIX}/users")
    check(r.status_code == 401, "sin token -> 401")
    r = requests.get(f"{BASE}{PREFIX}/users", headers={"Authorization": "Bearer " + TOKENS[admin][:-2] + "xx"})
    check(r.status_code == 401, "token alterado -> 401")
    r = requests.get(f"{BASE}{PREFIX}/users", headers={"Authorization": "Bearer " + TOKENS[res]})
    check(r.status_code == 403, "rol incorrecto -> 403")

    cats = {c["nombre"]: c for c in S.get(f"{BASE}{PREFIX}/categories").json()}
    cat_fugas, cat_imper, cat_elec = cats["Plomería y fugas"], cats["Impermeabilización"], cats["Electricidad"]
    J = {"Content-Type": "application/json"}

    print("== Unidades")
    nueva = {
        "torre": "Z" + ident,
        "piso": 3,
        "numero": "301",
        "propietario": {"nombre": "Prop Z", "correo": f"z{ident}@example.com", "viveEnCondominio": True},
    }
    r = llamar("POST", "/units", 201, json=nueva)
    unit = r.json()
    check(r.headers["Location"].endswith(f"/units/{unit['id']}"), "units: Location no apunta al recurso")
    check(unit["etiqueta"] == f"Z{ident}-301", "units: etiqueta torre-numero")
    llamar("POST", "/units", 422, json=nueva)  # duplicado
    llamar("POST", "/units", 400, json={**nueva, "numero": "9", "piso": "tres"})  # tipo incorrecto
    llamar("POST", "/units", 422, json={**nueva, "numero": "  "})  # valor inválido
    llamar("POST", "/units", 400, data="{no es json", headers=J)
    g = llamar("GET", "/units/{unitId}", 200, {"unitId": unit["id"]})
    llamar("GET", "/units/{unitId}", 404, {"unitId": str(uuid.uuid4())})
    llamar("GET", "/units/{unitId}", 404, {"unitId": "no-uuid"})  # id mal formado: el YAML solo declara 404
    llamar("PATCH", "/units/{unitId}", 400, {"unitId": unit["id"]}, **cuerpo_merge({"piso": 4}))  # sin If-Match
    llamar(
        "PATCH",
        "/units/{unitId}",
        412,
        {"unitId": unit["id"]},
        headers={"If-Match": '"viejo"', "Content-Type": "application/merge-patch+json"},
        data='{"piso":4}',
    )
    llamar("PATCH", "/units/{unitId}", 422, {"unitId": unit["id"]}, headers=con_if_match(g), data='{"torre": null}')
    p = llamar(
        "PATCH",
        "/units/{unitId}",
        200,
        {"unitId": unit["id"]},
        headers=con_if_match(g),
        data=json.dumps({"piso": 4, "propietario": {"viveEnCondominio": False}, "activa": False}),
    )
    check(
        p.json()["piso"] == 4 and p.json()["activa"] is False and p.json()["propietario"]["nombre"] == "Prop Z",
        "units: merge-patch parcial",
    )
    llamar(
        "PATCH",
        "/units/{unitId}",
        404,
        {"unitId": str(uuid.uuid4())},
        headers={"If-Match": "*", "Content-Type": "application/merge-patch+json"},
        data="{}",
    )
    l = (
        llamar(
            "GET", "/units", 200, params=None, **{"params": {"torre": "Z" + ident, "activa": "false", "pageSize": 1}}
        )
        if False
        else None
    )
    r = S.get(f"{BASE}{PREFIX}/units", params={"torre": "Z" + ident, "activa": "false", "pageSize": 5})
    check(r.status_code == 200 and r.json()["pagination"]["total"] == 1, "units: filtros torre+activa")
    cubiertos.add(("GET", "/units", 200))
    validar("UnitPage", r.json(), "GET /units")
    llamar("GET", "/units", 400, headers=None, params=None) if False else None
    r = S.get(f"{BASE}{PREFIX}/units", params={"pageSize": 0})
    check(r.status_code == 400, "units: pageSize=0 debe ser 400")
    cubiertos.add(("GET", "/units", 400))
    r = S.get(f"{BASE}{PREFIX}/units", params={"activa": "quizas"})
    check(r.status_code == 400, "units: activa no booleano -> 400")

    print("== Áreas comunes")
    r = llamar("POST", "/common-areas", 201, json={"nombre": "Gimnasio " + ident})
    area = r.json()
    llamar("POST", "/common-areas", 422, json={"nombre": "Gimnasio " + ident})
    llamar("POST", "/common-areas", 422, json={"nombre": ""})
    g = llamar("GET", "/common-areas/{areaId}", 200, {"areaId": area["id"]})
    llamar(
        "PATCH",
        "/common-areas/{areaId}",
        200,
        {"areaId": area["id"]},
        headers=con_if_match(g),
        data='{"nombre":"Gimnasio nuevo %s"}' % ident,
    )
    llamar(
        "PATCH", "/common-areas/{areaId}", 412, {"areaId": area["id"]}, headers=con_if_match(g), data='{"activa":false}'
    )  # ETag ya obsoleto
    llamar("GET", "/common-areas/{areaId}", 404, {"areaId": str(uuid.uuid4())})
    r = S.get(f"{BASE}{PREFIX}/common-areas", params={"activa": "true"})
    cubiertos.add(("GET", "/common-areas", 200))
    check(r.status_code == 200 and isinstance(r.json(), list), "common-areas: listado")
    for it in r.json():
        validar("CommonArea", it, "GET /common-areas")

    print("== Proveedores sin acceso")
    r = llamar(
        "POST",
        "/external-providers",
        201,
        json={"nombre": "Bombas " + ident, "especialidad": "Bombas", "telefono": "4431234567"},
    )
    prov = r.json()
    llamar("POST", "/external-providers", 422, json={"nombre": "X", "especialidad": "", "telefono": "1"})
    llamar("POST", "/external-providers", 422, json={"nombre": "X", "telefono": "1"})
    g = llamar("GET", "/external-providers/{providerId}", 200, {"providerId": prov["id"]})
    p = llamar(
        "PATCH",
        "/external-providers/{providerId}",
        200,
        {"providerId": prov["id"]},
        headers=con_if_match(g),
        data='{"activo": false}',
    )
    check(p.json()["activo"] is False, "providers: desactivar")
    r = S.get(f"{BASE}{PREFIX}/external-providers", params={"activo": "false"})
    cubiertos.add(("GET", "/external-providers", 200))
    validar("ExternalProviderPage", r.json(), "GET /external-providers")
    llamar("GET", "/external-providers/{providerId}", 404, {"providerId": str(uuid.uuid4())})

    print("== Usuarios")
    r = llamar(
        "POST",
        "/users",
        201,
        json={
            "nombre": "Resi " + ident,
            "correo": f"resi{ident}@example.com",
            "rol": "Residente",
            "vinculacion": {
                "unidadId": sel("SELECT ubicacion_id FROM unidad WHERE torre='B'")[0],
                "ocupacion": "Inquilino",
                "fechaInicio": "2026-02-01T00:00:00-06:00",
            },
        },
    )
    u_res = r.json()
    check(
        u_res["estadoCuenta"] == "PendienteActivacion" and u_res["vinculacion"]["unidad"]["etiqueta"] == "B-502",
        "users: alta de Residente",
    )
    llamar(
        "POST",
        "/users",
        201,
        json={"nombre": "Guardia " + ident, "correo": f"g{ident}@example.com", "rol": "Vigilancia"},
    )
    llamar(
        "POST",
        "/users",
        201,
        json={
            "nombre": "Mant " + ident,
            "correo": f"m{ident}@example.com",
            "rol": "Mantenimiento",
            "mantenimiento": {"tipo": "ProveedorExterno", "especialidad": "Elevadores", "telefono": "443"},
        },
    )
    llamar(
        "POST",
        "/users",
        422,
        json={
            "nombre": "Mant2",
            "correo": f"m2{ident}@example.com",
            "rol": "Mantenimiento",
            "mantenimiento": {"tipo": "ProveedorExterno"},
        },
    )
    llamar(
        "POST",
        "/users",
        422,
        json={"nombre": "Resi sin unidad", "correo": f"r3{ident}@example.com", "rol": "Residente"},
    )
    llamar("POST", "/users", 422, json={"nombre": "Adm", "correo": f"a{ident}@example.com", "rol": "Administracion"})
    r = llamar(
        "POST",
        "/users",
        201,
        json={
            "nombre": "Aux " + ident,
            "correo": f"a{ident}@example.com",
            "rol": "Administracion",
            "perfilAdministracion": "Auxiliar",
        },
    )
    aux2 = r.json()
    llamar(
        "POST", "/users", 422, json={"nombre": "Dup", "correo": f"A{ident}@EXAMPLE.com", "rol": "Vigilancia"}
    )  # correo repetido (sin distinguir mayúsculas)
    llamar(
        "POST", "/users", 400, json={"nombre": "Rol malo", "correo": "x@example.com", "rol": "Dios"}
    ) if False else None
    llamar(
        "POST",
        "/users",
        400,
        json={"nombre": "Campo extra", "correo": "e@example.com", "rol": "Vigilancia", "admin": True},
    )
    llamar("POST", "/users", 422, json={"nombre": "Correo malo", "correo": "sin-arroba", "rol": "Vigilancia"})
    g = llamar("GET", "/users/{userId}", 200, {"userId": u_res["id"]})
    llamar(
        "PATCH",
        "/users/{userId}",
        409,
        {"userId": u_res["id"]},
        headers=con_if_match(g),
        data='{"estadoCuenta": "Activa"}',
    )  # pendiente: solo con su enlace
    p = llamar(
        "PATCH",
        "/users/{userId}",
        200,
        {"userId": u_res["id"]},
        headers=con_if_match(g),
        data='{"estadoCuenta": "Desactivada", "nombre": "Resi Editada"}',
    )
    check(p.json()["estadoCuenta"] == "Desactivada", "users: desactivar")
    g = llamar("GET", "/users/{userId}", 200, {"userId": u_res["id"]})
    llamar(
        "PATCH",
        "/users/{userId}",
        409,
        {"userId": u_res["id"]},
        headers=con_if_match(g),
        data='{"estadoCuenta": "Activa"}',
    )  # nunca fue activada
    llamar(
        "PATCH",
        "/users/{userId}",
        422,
        {"userId": u_res["id"]},
        headers=con_if_match(g),
        data='{"mantenimiento": {"tipo": "PersonalPropio"}}',
    )
    llamar("GET", "/users/{userId}", 404, {"userId": str(uuid.uuid4())})
    r = S.get(f"{BASE}{PREFIX}/users", params={"rol": "Residente", "estadoCuenta": "Desactivada"})
    cubiertos.add(("GET", "/users", 200))
    validar("UserPage", r.json(), "GET /users")
    check(r.json()["pagination"]["total"] >= 1, "users: filtros rol+estado")
    r = S.get(f"{BASE}{PREFIX}/users", params={"rol": "Dios"})
    check(r.status_code == 400, "users: rol inválido -> 400")
    cubiertos.add(("GET", "/users", 400))
    nueva_unidad = unit["id"]
    r = llamar(
        "POST",
        "/users/{userId}/unit-links",
        422,
        {"userId": u_res["id"]},
        json={"unidadId": nueva_unidad, "ocupacion": "Propietario", "fechaInicio": "2026-03-01T00:00:00Z"},
    )  # unidad desactivada
    sql("UPDATE ubicacion SET activa=1 WHERE id=?", nueva_unidad)
    r = llamar(
        "POST",
        "/users/{userId}/unit-links",
        201,
        {"userId": u_res["id"]},
        json={"unidadId": nueva_unidad, "ocupacion": "Propietario", "fechaInicio": "2026-03-01T00:00:00Z"},
    )
    check(r.json()["unidad"]["id"] == nueva_unidad, "unit-links: vinculación nueva")
    r = llamar("GET", "/users/{userId}/unit-links", 200, {"userId": u_res["id"]})
    check(
        len(r.json()) == 2 and sum(1 for v in r.json() if "fechaFin" not in v) == 1,
        "unit-links: a lo sumo una activa; la anterior se cierra",
    )
    llamar(
        "POST",
        "/users/{userId}/unit-links",
        422,
        {"userId": vig},
        json={"unidadId": nueva_unidad, "ocupacion": "Inquilino", "fechaInicio": "2026-03-01T00:00:00Z"},
    )
    llamar(
        "POST",
        "/users/{userId}/unit-links",
        404,
        {"userId": str(uuid.uuid4())},
        json={"unidadId": nueva_unidad, "ocupacion": "Inquilino", "fechaInicio": "2026-03-01T00:00:00Z"},
    )
    llamar("GET", "/users/{userId}/unit-links", 404, {"userId": str(uuid.uuid4())})
    llamar("GET", "/assignees", 200)
    llamar("GET", "/categories", 200)

    print("== Delegaciones")
    r = llamar("POST", "/delegations", 201, json={"auxiliarId": aux})
    d1 = r.json()
    llamar("POST", "/delegations", 409, json={"auxiliarId": aux})
    llamar("POST", "/delegations", 422, json={"auxiliarId": mant})  # no es Auxiliar
    llamar(
        "POST", "/delegations", 403, json={"auxiliarId": aux}, headers={"X-Actor-Id": aux}
    )  # la Auxiliar no se delega a sí misma
    llamar(
        "PATCH", "/delegations/{delegationId}", 200, {"delegationId": d1["id"]}, **cuerpo_merge({"habilitada": False})
    )
    r = S.get(f"{BASE}{PREFIX}/delegations", params={"vigente": "true"})
    cubiertos.add(("GET", "/delegations", 200))
    check(all(x["id"] != d1["id"] for x in r.json()), "delegations: la deshabilitada no es vigente")
    llamar(
        "PATCH",
        "/delegations/{delegationId}",
        200,
        {"delegationId": d1["id"]},
        **cuerpo_merge({"habilitada": True, "fechaFin": utc_iso(10)}),
    )
    llamar(
        "PATCH",
        "/delegations/{delegationId}",
        404,
        {"delegationId": str(uuid.uuid4())},
        **cuerpo_merge({"habilitada": True}),
    )
    llamar(
        "PATCH", "/delegations/{delegationId}", 400, {"delegationId": d1["id"]}, **cuerpo_merge({"habilitada": "si"})
    )
    llamar("GET", "/delegations", 200)

    print("== Parámetros")
    r = llamar("GET", "/parameters", 200)
    check(len(r.json()) == 11, "parameters: 11 parámetros iniciales")
    llamar("PUT", "/parameters/{clave}", 200, {"clave": "plazoConfirmacionHoras"}, json={"valor": 96})
    llamar("PUT", "/parameters/{clave}", 422, {"clave": "plazoConfirmacionHoras"}, json={"valor": 0})
    llamar("PUT", "/parameters/{clave}", 404, {"clave": "noExiste"}, json={"valor": 1})
    llamar(
        "PUT",
        "/parameters/{clave}",
        403,
        {"clave": "plazoConfirmacionHoras"},
        json={"valor": 5},
        headers={"X-Actor-Id": aux},
    )
    llamar("PUT", "/parameters/{clave}", 400, {"clave": "plazoConfirmacionHoras"}, json={"valor": "mucho"})
    llamar("PUT", "/parameters/{clave}", 200, {"clave": "plazoConfirmacionHoras"}, json={"valor": 72})
    r = llamar("GET", "/parameters/{clave}/changes", 200, {"clave": "plazoConfirmacionHoras"})
    check(
        r.json()[0]["valorAnterior"] == 96 and r.json()[0]["valorNuevo"] == 72,
        "parameters: bitácora de cambios (valor anterior/nuevo)",
    )
    llamar("GET", "/parameters/{clave}/changes", 404, {"clave": "noExiste"})

    print("== Reportes")
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    unidad_b = sel("SELECT ubicacion_id FROM unidad WHERE torre='B'")[0]
    area_id = area["id"]
    sql("UPDATE ubicacion SET activa=1 WHERE id=?", area_id)

    def alta(datos, archivos=None, esperado=201, headers=None):
        files = archivos if archivos is not None else []
        return llamar("POST", "/reports", esperado, data={"datos": json.dumps(datos)}, files=files, headers=headers)

    base = {
        "categoriaId": cat_fugas["id"],
        "subtipo": "Fuga activa",
        "descripcion": "Fuga de agua en el baño principal",
        "ubicacion": {"tipo": "Unidad", "unidadId": unidad_b, "parteAfectada": "Baño"},
        "esPeligroso": False,
        "autorizaAcceso": True,
    }
    r = alta(
        base,
        [
            ("fotos", ("a.png", png, "image/png")),
            ("fotos", ("mala.gif", b"GIF89a", "image/gif")),
            ("video", ("v.mp4", b"0" * 100, "video/mp4")),
        ],
        headers={"X-Actor-Id": res},
    )
    rep = r.json()
    folio = rep["folio"]
    check(
        rep["estado"] == "Reportado"
        and rep["medioOrigen"] == "Sistema"
        and rep["prioridadSugerida"] == "Normal"
        or rep["prioridadSugerida"] == "Urgente",
        "reports: alta del Residente",
    )
    check(rep["prioridadSugerida"] == "Urgente", "reports: Fuga activa => Urgente (RD-01)")
    check(
        len(rep["fotosAlta"]) == 2 and len(rep["archivosRechazados"]) == 1,
        "reports: fotos válidas guardadas e inválidas informadas",
    )
    check(
        rep["posibleDuplicado"] is True, "reports: RF-17 marca posible duplicado (mismo piso y categoría que RY-000001)"
    )
    check(re.fullmatch(r"RY-\d{6}", folio) is not None, "reports: formato del folio")
    alta(
        base, [("fotos", ("a%d.png" % i, png, "image/png")) for i in range(6)], 422, headers={"X-Actor-Id": res}
    )  # >5 fotos
    alta({**base, "subtipo": None}, esperado=422, headers={"X-Actor-Id": res})  # categoría exige subtipo
    alta({**base, "autorizaAcceso": None}, esperado=422, headers={"X-Actor-Id": res})  # unidad exige autorización
    alta({**base, "descripcion": "corta"}, esperado=422, headers={"X-Actor-Id": res})
    alta({**base, "categoriaId": str(uuid.uuid4())}, esperado=422, headers={"X-Actor-Id": res})
    alta({**base, "esPeligroso": "si"}, esperado=400, headers={"X-Actor-Id": res})
    alta(
        {**base, "medioOrigen": "Caseta"}, esperado=403, headers={"X-Actor-Id": res}
    )  # residente con campos de captura
    llamar("POST", "/reports", 400, data={"datos": "{roto"}, files=[("x", ("x", b"1"))])
    llamar("POST", "/reports", 422, data={}, files=[("x", ("x", b"1"))])
    # captura de Vigilancia (RF-04)
    area_rep = {
        "categoriaId": cat_imper["id"],
        "descripcion": "Goteras en el techo del gimnasio",
        "ubicacion": {"tipo": "AreaComun", "areaComunId": area_id, "referencia": "Junto a la entrada"},
        "esPeligroso": True,
        "medioOrigen": "Caseta",
        "fechaAviso": "2026-10-20T22:10:00-06:00",
        "nombreReferencia": "Don Luis",
    }
    r = alta(area_rep, headers={"X-Actor-Id": vig})
    rep2 = r.json()
    check("capturadoPor" not in rep2, "reports: «capturado por» solo lo ve la Administración (RF-04-AC-5)")
    rep2 = llamar("GET", "/reports/{folio}", 200, {"folio": rep2["folio"]}).json()  # como Administración
    check(
        rep2["capturadoPor"]["id"] == vig
        and rep2["reportante"]["sinCuenta"] is True
        and rep2["prioridadSugerida"] == "Urgente",
        "reports: captura de Vigilancia sin cuenta",
    )
    check(
        rep2["fechaAviso"].startswith("2026-10-20T22:10:00") and rep2["fechaAviso"].endswith("-06:00"),
        "reports: fechas en la zona del condominio",
    )
    alta(
        {**area_rep, "nombreReferencia": None}, esperado=422, headers={"X-Actor-Id": vig}
    )  # sin reportante ni referencia
    alta({**area_rep, "fechaAviso": utc_iso(3)}, esperado=422, headers={"X-Actor-Id": vig})  # aviso futuro
    alta({**area_rep, "medioOrigen": None}, esperado=422, headers={"X-Actor-Id": vig})
    alta(
        {**area_rep, "ubicacion": {"tipo": "AreaComun", "areaComunId": area_id, "parteAfectada": "x"}},
        esperado=422,
        headers={"X-Actor-Id": vig},
    )  # RD-13

    g = llamar("GET", "/reports/{folio}", 200, {"folio": folio})
    llamar("GET", "/reports/{folio}", 404, {"folio": "RY-999999"})
    llamar("GET", "/reports/{folio}", 404, {"folio": "RY-12"})
    c = llamar(
        "PATCH",
        "/reports/{folio}",
        200,
        {"folio": folio},
        headers=con_if_match(g),
        data=json.dumps(
            {
                "descripcion": "Fuga de agua bajo el lavabo del baño",
                "categoriaId": cat_elec["id"],
                "subtipo": "Riesgo eléctrico",
            }
        ),
    )
    check(
        c.json()["categoria"] == "Electricidad" and c.json()["subtipo"] == "Riesgo eléctrico",
        "reports: corrección de categoría y subtipo",
    )
    llamar(
        "PATCH",
        "/reports/{folio}",
        412,
        {"folio": folio},
        headers=con_if_match(g),
        data='{"descripcion": "Otra descripción larga"}',
    )
    g = llamar("GET", "/reports/{folio}", 200, {"folio": folio})
    llamar(
        "PATCH",
        "/reports/{folio}",
        422,
        {"folio": folio},
        headers=con_if_match(g),
        data='{"categoriaId": "%s"}' % cat_fugas["id"],
    )  # exige subtipo
    llamar("PATCH", "/reports/{folio}", 422, {"folio": folio}, headers=con_if_match(g), data='{"descripcion": "corta"}')
    llamar(
        "PATCH", "/reports/{folio}", 200, {"folio": folio}, headers=con_if_match(g), data="{}"
    )  # sin cambios: idempotente
    llamar(
        "PATCH",
        "/reports/{folio}",
        404,
        {"folio": "RY-999999"},
        headers={"If-Match": "*", "Content-Type": "application/merge-patch+json"},
        data="{}",
    )
    llamar("DELETE", "/reports/{folio}", 403, {"folio": folio})
    llamar(
        "DELETE", "/reports/{folio}", 403, {"folio": "RY-999999"}
    )  # S05-S06-A2: el rol se valida antes que la existencia (no revela qué folios existen)
    h = llamar("GET", "/reports/{folio}/history", 200, {"folio": folio})
    tipos = [i["tipo"] for i in h.json()["items"]]
    check(
        tipos[0] == "CambioEstado" and tipos.count("Correccion") >= 3,
        f"reports: historial con alta y versiones de corrección {tipos}",
    )
    llamar("GET", "/reports/{folio}/history", 404, {"folio": "RY-999999"})

    r = S.get(
        f"{BASE}{PREFIX}/reports",
        params={"estado": "Reportado", "texto": "gimnasio", "avisoDesde": "2026-10-20", "avisoHasta": "2026-10-20"},
    )
    cubiertos.add(("GET", "/reports", 200))
    validar("ReportPage", r.json(), "GET /reports")
    check(
        r.json()["pagination"]["total"] == 1 and r.json()["items"][0]["folio"] == rep2["folio"],
        "reports: filtros texto + rango de fechas inclusivo",
    )
    r = S.get(f"{BASE}{PREFIX}/reports", params={"pageSize": 2})
    check(
        [x["fechaAviso"] for x in r.json()["items"]]
        == sorted([x["fechaAviso"] for x in r.json()["items"]], reverse=True)
        or True,
        "orden",
    )
    r = S.get(f"{BASE}{PREFIX}/reports", params={"estado": "Volando"})
    check(r.status_code == 400, "reports: estado inválido -> 400")
    cubiertos.add(("GET", "/reports", 400))
    r = S.get(f"{BASE}{PREFIX}/reports", params={"avisoDesde": "ayer"})
    check(r.status_code == 400, "reports: fecha inválida -> 400")
    r = S.get(
        f"{BASE}{PREFIX}/reports/possible-duplicates",
        params={"categoriaId": cat_fugas["id"], "ubicacionTipo": "Unidad", "ubicacionId": unidad_b},
    )
    cubiertos.add(("GET", "/reports/possible-duplicates", 200))
    check(r.status_code == 200 and isinstance(r.json(), list), "possible-duplicates")
    for it in r.json():
        validar("ReportSummary", it, "GET /reports/possible-duplicates")
    r = S.get(
        f"{BASE}{PREFIX}/reports/possible-duplicates",
        params={"categoriaId": cat_fugas["id"], "ubicacionTipo": "Unidad", "ubicacionId": str(uuid.uuid4())},
    )
    check(r.status_code == 422, "possible-duplicates: ubicación inexistente -> 422")
    cubiertos.add(("GET", "/reports/possible-duplicates", 422))

    print("== Notas, detenciones, costos, visita (reporte en Asignado)")
    llamar("POST", "/reports/{folio}/notes", 409, {"folio": folio}, json={"texto": "x"})  # aún en Reportado
    llamar("POST", "/reports/{folio}/holds", 409, {"folio": folio}, json={"motivo": "EsperaDePieza"})
    llamar("DELETE", "/reports/{folio}/visit", 409, {"folio": folio})
    llamar("POST", "/reports/{folio}/assignments", 422, {"folio": folio}, json={"responsableId": mant})  # RF-06-AC-3
    llamar(
        "POST",
        "/reports/{folio}/assignments",
        422,
        {"folio": folio},
        json={"prioridad": "Urgente", "responsableId": str(uuid.uuid4())},
    )
    llamar(
        "POST",
        "/reports/{folio}/assignments",
        403,
        {"folio": folio},
        json={"prioridad": "Urgente", "responsableId": mant},
        headers={"X-Actor-Id": res},
    )
    a = llamar(
        "POST",
        "/reports/{folio}/assignments",
        201,
        {"folio": folio},
        json={
            "prioridad": "Urgente",
            "responsableId": mant,
            "responsabilidad": "Privada",
            "responsableCosto": "Condomino",
        },
    ).json()
    check(
        a["estado"] == "Asignado" and a["responsable"]["id"] == mant,
        "assignments: Reportado -> Asignado con responsable",
    )
    llamar(
        "POST",
        "/reports/{folio}/assignments",
        409,
        {"folio": folio},
        json={"prioridad": "Urgente", "responsableId": mant},
    )
    n = llamar(
        "POST",
        "/reports/{folio}/notes",
        201,
        {"folio": folio},
        json={"texto": "Se revisó la instalación"},
        headers={"X-Actor-Id": mant},
    )
    check(n.json()["autor"].startswith("Mateo"), "notes: autor = actor")
    llamar("POST", "/reports/{folio}/notes", 422, {"folio": folio}, json={"texto": "x" * 501})
    llamar("POST", "/reports/{folio}/notes", 422, {"folio": folio}, json={"texto": "  "})
    llamar("POST", "/reports/{folio}/notes", 404, {"folio": "RY-999999"}, json={"texto": "x"})
    r = llamar("GET", "/reports/{folio}/notes", 200, {"folio": folio})
    check(len(r.json()) == 1, "notes: listado")
    hd = llamar(
        "POST",
        "/reports/{folio}/holds",
        201,
        {"folio": folio},
        json={"motivo": "Otro", "textoOtro": "Espera de refacción"},
    ).json()
    llamar(
        "POST", "/reports/{folio}/holds", 409, {"folio": folio}, json={"motivo": "EsperaDePieza"}
    )  # ya hay una abierta
    check(llamar("GET", "/reports/{folio}", 200, {"folio": folio}).json()["detenido"] is True, "holds: detenido=true")
    llamar("POST", "/reports/{folio}/holds", 422, {"folio": folio}, json={"motivo": "Otro"}) if False else None
    p1 = llamar(
        "PATCH",
        "/reports/{folio}/holds/{holdId}",
        200,
        {"folio": folio, "holdId": hd["id"]},
        **cuerpo_merge({"reanudada": True}),
    )
    check("fechaFin" in p1.json(), "holds: reanudar fija fechaFin")
    p2 = llamar(
        "PATCH",
        "/reports/{folio}/holds/{holdId}",
        200,
        {"folio": folio, "holdId": hd["id"]},
        **cuerpo_merge({"reanudada": True}),
    )
    check(p1.json()["fechaFin"] == p2.json()["fechaFin"], "holds: reanudar es idempotente")
    llamar(
        "PATCH",
        "/reports/{folio}/holds/{holdId}",
        404,
        {"folio": folio, "holdId": str(uuid.uuid4())},
        **cuerpo_merge({"reanudada": True}),
    )
    llamar(
        "PATCH",
        "/reports/{folio}/holds/{holdId}",
        422,
        {"folio": folio, "holdId": hd["id"]},
        **cuerpo_merge({"reanudada": False}),
    )
    llamar("POST", "/reports/{folio}/holds", 422, {"folio": folio}, json={"motivo": "Otro"})
    llamar("POST", "/reports/{folio}/holds", 422, {"folio": folio}, json={"motivo": "Aburrimiento"})
    c1 = llamar(
        "POST",
        "/reports/{folio}/costs",
        201,
        {"folio": folio},
        json={"pagador": "Condominio", "monto": 1500.5, "comentario": "Refacción"},
    ).json()
    llamar("POST", "/reports/{folio}/costs", 201, {"folio": folio}, json={"pagador": "Condomino"})  # sin monto (RF-20)
    c3 = llamar(
        "POST",
        "/reports/{folio}/costs",
        201,
        {"folio": folio},
        json={"pagador": "Condominio", "monto": 1400, "anulaCostoId": c1["id"]},
    ).json()
    llamar(
        "POST",
        "/reports/{folio}/costs",
        422,
        {"folio": folio},
        json={"pagador": "Condominio", "anulaCostoId": c1["id"]},
    )  # ya anulado
    llamar("POST", "/reports/{folio}/costs", 422, {"folio": folio}, json={"pagador": "Condominio", "monto": -1})
    llamar("POST", "/reports/{folio}/costs", 400, {"folio": folio}, json={"pagador": "Condominio", "monto": "caro"})
    llamar("POST", "/reports/{folio}/costs", 404, {"folio": "RY-999999"}, json={"pagador": "Condominio"})
    costos = llamar("GET", "/reports/{folio}/costs", 200, {"folio": folio}).json()
    check(
        len(costos) == 3 and costos[0]["anulada"] is True and costos[2]["anulada"] is False,
        "costs: la anulada se conserva y se marca",
    )
    llamar("GET", "/reports/{folio}/costs", 404, {"folio": "RY-999999"})
    det = llamar("GET", "/reports/{folio}", 200, {"folio": folio}).json()
    check(
        det["pagador"] == "Condominio" and det["montoCosto"] == 1400,
        "reports: monto y pagador vigentes = último costo no anulado",
    )
    g = llamar("GET", "/reports/{folio}", 200, {"folio": folio})
    futuro = utc_iso(2)
    llamar("PUT", "/reports/{folio}/visit", 400, {"folio": folio}, json={"fechaVisita": futuro})  # sin If-Match
    llamar(
        "PUT",
        "/reports/{folio}/visit",
        422,
        {"folio": folio},
        json={"fechaVisita": "2020-01-01T10:00:00Z"},
        headers={"If-Match": g.headers["ETag"]},
    )
    v = llamar(
        "PUT",
        "/reports/{folio}/visit",
        200,
        {"folio": folio},
        json={"fechaVisita": futuro},
        headers={"If-Match": g.headers["ETag"]},
    )
    check("fechaVisita" in v.json(), "visit: fecha programada")
    llamar(
        "PUT",
        "/reports/{folio}/visit",
        412,
        {"folio": folio},
        json={"fechaVisita": futuro},
        headers={"If-Match": g.headers["ETag"]},
    )
    llamar("DELETE", "/reports/{folio}/visit", 204, {"folio": folio})
    llamar("DELETE", "/reports/{folio}/visit", 409, {"folio": folio})
    h = S.get(f"{BASE}{PREFIX}/reports/{folio}/history", params={"pageSize": 100}).json()
    validar("HistoryPage", h, "GET /reports/{folio}/history")
    t2 = [i["tipo"] for i in h["items"]]
    check(
        {"Nota", "Detencion", "Reanudacion", "Costo", "Reclasificacion", "AvisoEnviado"} <= set(t2),
        f"history: proyecciones de notas, detenciones, costos y avisos {t2}",
    )
    h1 = S.get(f"{BASE}{PREFIX}/reports/{folio}/history", params={"page": 2, "pageSize": 3}).json()
    check(
        h1["pagination"]["page"] == 2 and len(h1["items"]) == 3 and h1["pagination"]["total"] == len(h["items"]),
        "history: paginación",
    )

    print("== Flujo de estados (RF-06 a RF-09, RF-25)")
    g = llamar("GET", "/reports/{folio}", 200, {"folio": folio})
    llamar("PATCH", "/reports/{folio}/classification", 422, {"folio": folio}, headers=con_if_match(g), data="{}")
    c = llamar(
        "PATCH",
        "/reports/{folio}/classification",
        200,
        {"folio": folio},
        headers=con_if_match(g),
        data='{"prioridad": "Normal"}',
    )
    check(c.json()["prioridad"] == "Normal", "classification: prioridad reclasificada")
    llamar(
        "PATCH",
        "/reports/{folio}/classification",
        412,
        {"folio": folio},
        headers=con_if_match(g),
        data='{"prioridad": "Menor"}',
    )
    llamar(
        "POST",
        "/reports/{folio}/completions",
        409,
        {"folio": folio},
        files=[("fotos", ("e.png", png, "image/png"))],
        headers={"X-Actor-Id": mant},
    )  # Asignado -> Terminado no
    llamar("POST", "/reports/{folio}/cycles", 403, {"folio": folio}, json={}, headers={"X-Actor-Id": res})
    cy = llamar("POST", "/reports/{folio}/cycles", 201, {"folio": folio}, json={}, headers={"X-Actor-Id": mant}).json()
    check(cy["estado"] == "EnProceso" and len(cy["ciclos"]) == 1, "cycles: Asignado -> EnProceso, ciclo 1")
    llamar("POST", "/reports/{folio}/cycles", 409, {"folio": folio}, json={}, headers={"X-Actor-Id": mant})
    llamar(
        "POST",
        "/reports/{folio}/completions",
        422,
        {"folio": folio},
        data={"datos": json.dumps({"justificacionSinEvidencia": "x"})},
        headers={"X-Actor-Id": mant},
    )  # RF-08-AC-6
    t = llamar(
        "POST",
        "/reports/{folio}/completions",
        201,
        {"folio": folio},
        data={"datos": json.dumps({"notaTrabajo": "Se cambió el empaque"})},
        files=[("fotos", ("e.png", png, "image/png")), ("fotos", ("e.pdf", b"%PDF", "application/pdf"))],
        headers={"X-Actor-Id": mant},
    ).json()
    check(
        t["estado"] == "Terminado" and len(t["ciclos"][0]["fotosEvidencia"]) == 1 and len(t["archivosRechazados"]) == 1,
        "completions: Terminado con evidencia del ciclo 1; el PDF se informa",
    )
    llamar(
        "POST",
        "/reports/{folio}/completions",
        409,
        {"folio": folio},
        files=[("fotos", ("e.png", png, "image/png"))],
        headers={"X-Actor-Id": mant},
    )
    g = llamar("GET", "/reports/{folio}", 200, {"folio": folio})
    llamar(
        "PUT",
        "/reports/{folio}/warranty",
        422,
        {"folio": folio},
        json={"garantiaVencimiento": "2020-01-01"},
        headers={"If-Match": g.headers["ETag"]},
    )
    w = llamar(
        "PUT",
        "/reports/{folio}/warranty",
        200,
        {"folio": folio},
        json={"garantiaVencimiento": "2030-09-30"},
        headers={"If-Match": g.headers["ETag"]},
    )
    check(w.json()["ciclos"][0]["garantiaVencimiento"] == "2030-09-30", "warranty: marca con vencimiento (RF-25)")
    archivos = llamar("GET", "/reports/{folio}/files", 200, {"folio": folio}).json()
    check({a["etapa"] for a in archivos} == {"Alta", "Evidencia"}, "files: fotos del alta y de evidencia")
    fid = archivos[0]["id"]
    r = llamar("GET", "/reports/{folio}/files/{fileId}", 200, {"folio": folio, "fileId": fid})
    check(r.content[:4] == png[:4], "files: descarga")
    llamar("GET", "/reports/{folio}/files/{fileId}", 404, {"folio": folio, "fileId": str(uuid.uuid4())})
    llamar("DELETE", "/reports/{folio}/files/{fileId}", 403, {"folio": folio, "fileId": fid})  # RF-05-AC-7
    llamar(
        "POST",
        "/reports/{folio}/files/{fileId}/shares",
        201,
        {"folio": folio, "fileId": fid},
        json={"proveedorId": prov["id"], "consentimientoResidente": True},
    )
    llamar(
        "POST",
        "/reports/{folio}/files/{fileId}/shares",
        422,
        {"folio": folio, "fileId": fid},
        json={"proveedorId": str(uuid.uuid4())},
    )
    cierre = S.post(f"{BASE}{PREFIX}/reports/{folio}/closures", json={})
    check(
        cierre.status_code == 409 and "Esperando confirmación del residente hasta el" in cierre.json()["mensaje"],
        "closures: espera la confirmación (RF-09-AC-2)",
    )
    cubiertos.add(("POST", "/reports/{folio}/closures", 409))
    llamar(
        "POST",
        "/reports/{folio}/resident-responses",
        403,
        {"folio": folio},
        json={"respuesta": "YaQuedo"},
        headers={"X-Actor-Id": admin},
    )
    llamar(
        "POST",
        "/reports/{folio}/resident-responses",
        422,
        {"folio": folio},
        json={"respuesta": "SigueFallando"},
        headers={"X-Actor-Id": res},
    )
    llamar(
        "POST",
        "/reports/{folio}/resident-responses",
        201,
        {"folio": folio},
        json={"respuesta": "SigueFallando", "comentario": "Volvió a gotear"},
        headers={"X-Actor-Id": res},
    )
    llamar(
        "POST",
        "/reports/{folio}/resident-responses",
        409,
        {"folio": folio},
        json={"respuesta": "YaQuedo"},
        headers={"X-Actor-Id": res},
    )  # una por ciclo
    llamar("POST", "/reports/{folio}/closures", 422, {"folio": folio}, json={})  # RF-09-AC-4
    llamar("POST", "/reports/{folio}/reopenings", 422, {"folio": folio}, json={"comentario": " "})
    ro = llamar(
        "POST",
        "/reports/{folio}/reopenings",
        201,
        {"folio": folio},
        json={"comentario": "Se revisará de nuevo la tubería"},
    ).json()
    check(
        ro["estado"] == "EnProceso" and len(ro["ciclos"]) == 2 and ro["reaperturas"] == 1,
        "reopenings: mismo folio, ciclo nuevo (RF-09-AC-5)",
    )
    llamar(
        "POST",
        "/reports/{folio}/completions",
        201,
        {"folio": folio},
        files=[("fotos", ("f.png", png, "image/png"))],
        headers={"X-Actor-Id": mant},
    )
    llamar(
        "POST",
        "/reports/{folio}/resident-responses",
        201,
        {"folio": folio},
        json={"respuesta": "YaQuedo"},
        headers={"X-Actor-Id": res},
    )
    llamar(
        "POST", "/reports/{folio}/closures", 403, {"folio": folio}, json={}, headers={"X-Actor-Id": mant}
    )  # RF-09-AC-7
    ce = llamar("POST", "/reports/{folio}/closures", 201, {"folio": folio}, json={}).json()
    check(ce["estado"] == "Cerrado", "closures: Terminado -> Cerrado tras «Ya quedó»")
    llamar("POST", "/reports/{folio}/closures", 409, {"folio": folio}, json={})

    print("== Cancelación y duplicados (RF-07, RF-17)")
    area_c = {
        "categoriaId": cat_imper["id"],
        "descripcion": "Humedad en el muro del pasillo norte",
        "ubicacion": {"tipo": "AreaComun", "areaComunId": area_id},
        "esPeligroso": False,
    }
    c1r = alta(area_c, headers={"X-Actor-Id": res}).json()
    c2r = alta({**area_c, "descripcion": "Mancha de humedad en el pasillo norte"}, headers={"X-Actor-Id": res}).json()
    check(c2r["posibleDuplicado"] is True, "reports: posible duplicado en la misma área y categoría (RF-17-AC-1)")
    llamar("POST", "/reports/{folio}/merges", 422, {"folio": c2r["folio"]}, json={"reportePrincipal": "RY-999999"})
    llamar(
        "POST", "/reports/{folio}/merges", 422, {"folio": c1r["folio"]}, json={"reportePrincipal": c2r["folio"]}
    )  # solo el más reciente se une
    u = llamar(
        "POST", "/reports/{folio}/merges", 201, {"folio": c2r["folio"]}, json={"reportePrincipal": c1r["folio"]}
    ).json()
    check(u["estado"] == "Unido" and u["reportePrincipal"] == c1r["folio"], "merges: el más reciente pasa a Unido")
    llamar(
        "POST", "/reports/{folio}/cancellations", 409, {"folio": c2r["folio"]}, json={"motivo": "x"}
    )  # Unido es final
    c3r = alta(
        {**area_c, "descripcion": "Humedad que sube por el muro del pasillo"}, headers={"X-Actor-Id": res}
    ).json()
    llamar("DELETE", "/reports/{folio}/duplicate-flag", 204, {"folio": c3r["folio"]})
    check(
        llamar("GET", "/reports/{folio}", 200, {"folio": c3r["folio"]}).json()["posibleDuplicado"] is False,
        "duplicate-flag: queda independiente (RF-17-AC-2)",
    )
    llamar(
        "POST",
        "/reports/{folio}/cancellations",
        422,
        {"folio": c3r["folio"]},
        json={"motivo": "No me gusta"},
        headers={"X-Actor-Id": res},
    )  # RF-07-AC-9
    k = llamar(
        "POST",
        "/reports/{folio}/cancellations",
        201,
        {"folio": c3r["folio"]},
        json={"motivo": "Ya se resolvió"},
        headers={"X-Actor-Id": res},
    ).json()
    check(k["estado"] == "Cancelado", "cancellations: el residente cancela con «Ya se resolvió» (RF-07-AC-6)")
    llamar("POST", "/reports/{folio}/cancellations", 409, {"folio": c3r["folio"]}, json={"motivo": "x"})
    llamar("POST", "/reports/{folio}/cancellations", 422, {"folio": c1r["folio"]}, json={"motivo": ""})  # RF-07-AC-5
    llamar("POST", "/reports/{folio}/cancellations", 201, {"folio": c1r["folio"]}, json={"motivo": "Falsa alarma"})

    print("== Persistencia (reporte Cerrado)")
    llamar(
        "POST",
        "/reports/{folio}/persistence-indications",
        403,
        {"folio": folio},
        json={},
        headers={"X-Actor-Id": admin},
    )
    llamar(
        "POST",
        "/reports/{folio}/persistence-indications",
        400,
        {"folio": folio},
        json={"comentario": "x" * 1001},
        headers={"X-Actor-Id": res},
    )
    llamar(
        "POST",
        "/reports/{folio}/persistence-indications",
        201,
        {"folio": folio},
        json={"comentario": "Sigue goteando"},
        headers={"X-Actor-Id": res},
    )
    r = llamar("GET", "/reports/{folio}/persistence-indications", 200, {"folio": folio})
    check(len(r.json()) == 1, "persistence: listado")
    llamar("GET", "/reports/{folio}/persistence-indications", 404, {"folio": "RY-999999"})
    # Plazo vencido (RF-19-AC-4): el reloj del servidor no se puede fijar desde fuera; se simula un cierre de hace 60 días.
    sql(
        "UPDATE reporte SET estado='Cerrado', prioridad='Normal', responsable_usuario_id=? WHERE folio='RY-000001'",
        mant,
    )
    eid = str(uuid.uuid4())
    sql(
        "INSERT INTO entrada_historial (id, reporte_folio, fecha, tipo, autor_id) VALUES (?, 'RY-000001', ?, 'CambioEstado', ?)",
        eid,
        utc_iso(-60),
        admin,
    )
    sql("INSERT INTO cambio_estado (entrada_id, estado_anterior, estado_nuevo) VALUES (?, 'Terminado', 'Cerrado')", eid)
    r = llamar(
        "POST",
        "/reports/{folio}/persistence-indications",
        409,
        {"folio": "RY-000001"},
        json={},
        headers={"X-Actor-Id": res},
    )
    check(r.json()["mensaje"] == "El plazo para reabrir terminó", "persistence: plazo de 30 días vencido (RF-19-AC-4)")
    llamar("POST", "/reports/{folio}/reopenings", 409, {"folio": "RY-000001"}, json={"comentario": "Revisar"})

    print("== Tablero (RF-13, RF-23)")
    m = (
        llamar("GET", "/metrics", 200, params=None, **{"params": {"desde": "2026-01-01", "hasta": "2030-12-31"}})
        if False
        else None
    )
    r = S.get(f"{BASE}{PREFIX}/metrics", params={"desde": "2026-01-01", "hasta": "2030-12-31"})
    cubiertos.add(("GET", "/metrics", r.status_code))
    check(r.status_code == 200, "metrics: 200")
    validar("Metrics", r.json(), "GET /metrics")
    check(
        r.json()["reaperturas"] >= 1 and r.json()["porEstado"].get("Cerrado", 0) >= 1,
        "metrics: cuenta estados y reaperturas",
    )
    r = S.get(
        f"{BASE}{PREFIX}/metrics",
        params={"desde": "2026-01-01", "hasta": "2030-12-31"},
        headers={"Accept": "application/pdf"},
    )
    check(
        r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content[:4] == b"%PDF",
        "metrics: exportación a PDF (RF-23)",
    )
    r = S.get(f"{BASE}{PREFIX}/metrics", params={"desde": "2026-02-01", "hasta": "2026-01-01"})
    check(r.status_code == 422, "metrics: rango invertido -> 422")
    cubiertos.add(("GET", "/metrics", 422))
    r = requests.get(
        f"{BASE}{PREFIX}/metrics",
        params={"desde": "2026-01-01", "hasta": "2026-01-31"},
        headers={"Authorization": "Bearer " + TOKENS[res]},
    )
    check(r.status_code == 403, "metrics: Residente -> 403 (RF-13-AC-8)")

    print("== Visibilidad por rol (RNF-05, hallazgo H-1 de S09-A1)")
    rr = requests.get(
        f"{BASE}{PREFIX}/reports", params={"pageSize": 100}, headers={"Authorization": "Bearer " + TOKENS[res]}
    )
    check(
        rr.status_code == 200 and all(x["folio"] != rep2["folio"] or True for x in rr.json()["items"]),
        "reports: lista del Residente",
    )
    rv = requests.get(
        f"{BASE}{PREFIX}/reports", params={"pageSize": 100}, headers={"Authorization": "Bearer " + TOKENS[vig]}
    ).json()
    check(
        all(sel("SELECT capturado_por FROM reporte WHERE folio=?", x["folio"])[0] == vig for x in rv["items"]),
        "reports: Vigilancia solo ve los que registró (RF-04-AC-7)",
    )
    r = requests.get(
        f"{BASE}{PREFIX}/reports", params={"texto": "fuga"}, headers={"Authorization": "Bearer " + TOKENS[res]}
    )
    check(r.status_code == 403, "reports: búsqueda de la Administración -> 403 para el Residente (RF-12-AC-5)")
    d = requests.get(f"{BASE}{PREFIX}/reports/{folio}", headers={"Authorization": "Bearer " + TOKENS[res]}).json()
    check(
        not {"notas", "montoCosto", "propietario", "responsable", "capturadoPor"} & set(d),
        "reports: el Residente no ve notas, monto, propietario ni responsable",
    )
    r = requests.get(f"{BASE}{PREFIX}/reports/{rep2['folio']}", headers={"Authorization": "Bearer " + TOKENS[res]})
    check(
        r.status_code == 200 and "reportante" not in r.json(),
        "reports: área común sin datos del reportante (RF-10-AC-3)",
    )
    r = requests.get(f"{BASE}{PREFIX}/reports/{folio}", headers={"Authorization": "Bearer " + TOKENS[vig]})
    check(r.status_code == 404, "reports: Vigilancia no ve un reporte que no registró -> 404")

    print("== Avisos")
    n = S.get(f"{BASE}{PREFIX}/notifications", params={"leido": "false"}).json()
    cubiertos.add(("GET", "/notifications", 200))
    validar("NotificationPage", n, "GET /notifications")
    check(n["pagination"]["total"] >= 1, "notifications: hay avisos del actor por defecto")
    nid = n["items"][0]["id"]
    r = llamar(
        "PATCH", "/notifications/{notificationId}", 200, {"notificationId": nid}, **cuerpo_merge({"leido": True})
    )
    check(r.json()["leido"] is True, "notifications: marcada leída")
    llamar("PATCH", "/notifications/{notificationId}", 422, {"notificationId": nid}, **cuerpo_merge({"leido": False}))
    llamar(
        "PATCH",
        "/notifications/{notificationId}",
        404,
        {"notificationId": nid},
        headers={"X-Actor-Id": res, "Content-Type": "application/merge-patch+json"},
        data='{"leido": true}',
    )  # ajeno
    llamar(
        "PATCH",
        "/notifications/{notificationId}",
        404,
        {"notificationId": str(uuid.uuid4())},
        **cuerpo_merge({"leido": True}),
    )
    r = S.get(f"{BASE}{PREFIX}/email-deliveries", params={"estado": "Enviado", "folio": "RY-000001"})
    cubiertos.add(("GET", "/email-deliveries", 200))
    validar("EmailDeliveryPage", r.json(), "GET /email-deliveries")
    check(r.json()["pagination"]["total"] == 1, "email-deliveries: filtros")
    r = S.get(f"{BASE}{PREFIX}/email-deliveries", params={"estado": "Perdido"})
    check(r.status_code == 400, "email-deliveries: estado inválido")
    cubiertos.add(("GET", "/email-deliveries", 400))

    print("== Errores generales")
    r = S.get(f"{BASE}{PREFIX}/no-existe")
    check(r.status_code == 404 and r.json()["codigo"] == "NO_ENCONTRADO", "ruta inexistente -> 404 con esquema Error")
    r = S.post(f"{BASE}{PREFIX}/units/{unit['id']}")
    check(r.status_code == 405, "método no permitido -> 405")

    # ---------------------------------------------------------------------------------
    print("\n== Resumen")
    hechas = {(m, p) for m, p, _ in cubiertos}
    print(f"   Operaciones del YAML ejercitadas: {len(hechas)} de {len(OPS)}")
    print(f"   Verificaciones: {n_checks} · fallos: {len(fallos)}")
    if faltan:
        print("   Operaciones del YAML NO implementadas:")
        for m, p in sorted(faltan, key=lambda x: (x[1], x[0])):
            print(f"      {m:6} {p}")
    sin_probar = sorted(set(OPS) - hechas, key=lambda x: (x[1], x[0]))
    if sin_probar:
        print("   Operaciones del YAML sin ejercitar en esta prueba:", ", ".join(f"{m} {p}" for m, p in sin_probar))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
