"""Prueba de carga de RNF-03: p95 ≤ 2 s en RF-10, RF-12, RF-13 y RF-16 con 5,000 reportes y 20 usuarios concurrentes.

    python scripts/prueba_carga.py preparar             # BORRA la base de .env: demo + reportes hasta llegar a 5,000
    python scripts/prueba_carga.py preparar --continuar # si se interrumpió: sigue donde iba
    taskset -c 0 prlimit --as=1073741824 uvicorn app.main:app --port 8000 &    # 1 vCPU y 1 GB, como pide el SRS
    taskset -c 1 python scripts/prueba_carga.py medir --segundos 60            # el generador en otro núcleo

`preparar` usa el flujo real del API en el mismo proceso, con el reloj fijado (RNF-10), y reparte los reportes
en los últimos 4 años (unos 100 al mes, el volumen máximo de RNF-03) y en todos los estados.
`medir` simula 20 usuarios (residentes, Administración y Mantenimiento) que consultan sin pausa y
reporta, por requisito, número de peticiones, errores, mediana, p95 y máximo.
"""

import argparse
import asyncio
import json
import math
import random
import sqlite3
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TOTAL = 5000
PASSWORD = "Demo1234!"

DESCRIPCIONES = [
    ("Plomería y fugas", "Fuga activa", "Gotea agua del techo del baño cuando usan la regadera de arriba"),
    (
        "Plomería y fugas",
        "Drenaje tapado o desbordado",
        "El drenaje del patio de servicio se tapa cuando llueve fuerte",
    ),
    ("Iluminación", "Pasillo o área techada", "La lámpara del pasillo parpadea y luego se apaga por completo"),
    ("Iluminación", "Jardín o exterior", "Dos lámparas del andador del jardín no encienden en la noche"),
    ("Electricidad", "Otra", "El contacto de la cocina dejó de funcionar y huele a quemado"),
    ("Jardinería", None, "Hay una rama rota colgando sobre el andador principal del jardín"),
]


def _contexto(db) -> dict:
    """Ids de usuarios, categorías, subtipos, áreas comunes y la unidad de cada residente de la demo."""
    usuarios = {correo.split("@")[0]: i for correo, i in db.execute("SELECT correo, id FROM usuario")}
    subtipos: dict = {}
    for cat_id, nombre in db.execute("SELECT categoria_id, nombre FROM subtipo"):
        subtipos.setdefault(cat_id, []).append(nombre)
    vinculos = dict(
        db.execute("SELECT u.correo, v.unidad_id FROM vinculacion_unidad v JOIN usuario u ON u.id = v.residente_id")
    )
    return {
        "usuarios": usuarios,
        "cats": {n: i for i, n in db.execute("SELECT id, nombre FROM categoria")},
        "subtipos": subtipos,
        "areas": [a for (a,) in db.execute("SELECT ubicacion_id FROM area_comun")],
        "unidad": {
            "mariana": vinculos["residente@reportaya.demo"],
            "carlos": vinculos["carlos@reportaya.demo"],
            "ana": vinculos["ana@reportaya.demo"],
        },
        "ya": db.execute("SELECT COUNT(*) FROM reporte").fetchone()[0],
    }


def _alta(rnd, n: int, c: dict, aviso: datetime) -> tuple:
    """(quién reporta, datos del alta) de un reporte realista de la categoría elegida al azar."""
    nombre_cat, subtipo, texto = rnd.choice(DESCRIPCIONES)
    cat = c["cats"][nombre_cat]
    subtipo = subtipo if subtipo in c["subtipos"].get(cat, []) else (c["subtipos"].get(cat) or [None])[0]
    quien = rnd.choice(["mariana", "carlos", "ana", "vigilancia"])
    datos = {"categoriaId": cat, "descripcion": f"{texto} (#{n})", "esPeligroso": False}
    if quien == "vigilancia" or rnd.random() < 0.6:
        datos["ubicacion"] = {"tipo": "AreaComun", "areaComunId": rnd.choice(c["areas"])}
    else:
        datos["ubicacion"] = {"tipo": "Unidad", "unidadId": c["unidad"][quien], "parteAfectada": "Baño"}
        datos.update(autorizaAcceso=True, horariosAcceso="Por las tardes")
    if subtipo:
        datos["subtipo"] = subtipo
    if quien == "vigilancia":
        datos.update(medioOrigen="Caseta", fechaAviso=aviso.isoformat(), nombreReferencia="Residente en caseta")
    return quien, datos


def _avanzar(api, reloj, rnd, folio: str, aviso: datetime, hace: timedelta) -> None:
    """Lleva el reporte por el flujo real; los de los últimos 60 días quedan repartidos en los estados abiertos."""
    destino = rnd.random() if hace < timedelta(days=60) else 1.0
    pasos = (
        (
            0.35,
            timedelta(hours=2),
            "admin",
            "assignments",
            {
                "prioridad": rnd.choice(["Urgente", "Normal", "Normal", "Menor"]),
                "responsableId": api.ids["conserje"],
                "responsabilidad": "Comun",
                "responsableCosto": "Condominio",
            },
        ),
        (0.60, timedelta(hours=5), "conserje", "cycles", {}),
        (0.75, timedelta(hours=20), "conserje", "completions", None),
    )
    for umbral, despues, quien, recurso, cuerpo in pasos:
        if destino < umbral:
            return  # se queda en Reportado, Asignado (lista de Mantenimiento, RF-16) o En proceso
        reloj.fijar(aviso + despues)
        if recurso == "completions":
            api.terminar(quien, folio, notaTrabajo="Trabajo realizado y probado")
        else:
            api.post(quien, f"/reports/{folio}/{recurso}", json=cuerpo)
    if hace >= timedelta(days=6):  # los más recientes esperan la confirmación del residente (RF-09)
        reloj.fijar(aviso + timedelta(days=5))
        api.post("admin", f"/reports/{folio}/closures", json={})


def preparar(continuar: bool = False):
    from app import config, reloj
    from scripts import cargar_demo as demo

    if not continuar:
        demo.main()  # demo realista (16 reportes) como punto de partida
    db = sqlite3.connect(config.DATABASE_PATH)
    c = _contexto(db)
    demo_n = db.execute("SELECT COUNT(*) FROM reporte WHERE descripcion NOT LIKE '%(#%)'").fetchone()[0]
    db.close()
    clave_de = {"mantenimiento": "conserje", "residente": "mariana"}
    api = demo.Api({clave_de.get(k, k): v for k, v in c["usuarios"].items()})
    rnd = random.Random(2026)
    ahora = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    faltan = TOTAL - demo_n  # el calendario no cambia al continuar una generación interrumpida
    inicio = time.time()
    for i in range(c["ya"] - demo_n, faltan):
        hace = timedelta(days=(faltan - i) * 1460 / faltan + 1)  # del más antiguo (hace 4 años) al más reciente
        aviso = ahora - hace
        reloj.fijar(aviso)
        quien, datos = _alta(rnd, i + 1, c, aviso)
        _avanzar(api, reloj, rnd, api.reportar(quien, **datos), aviso, hace)
        if (i + 1) % 500 == 0:
            print(f"  {demo_n + i + 1} reportes · {time.time() - inicio:.0f} s", flush=True)
    reloj.liberar()
    print(f"Base lista: {TOTAL} reportes en {config.DATABASE_PATH} ({time.time() - inicio:.0f} s)")


def percentil_95(ordenados: list) -> float:
    """Percentil 95 por rango más cercano: el valor que deja al menos el 95 % de las muestras por debajo o igual."""
    return ordenados[math.ceil(0.95 * len(ordenados)) - 1]


def _resumen(tiempos: dict, errores: dict, lentas: list, segundos: int) -> dict:
    """Tabla por consulta (n, errores, mediana, p95, máximo) y veredicto de RNF-03."""
    filas = []
    for nombre in sorted(tiempos):
        t = sorted(tiempos[nombre])
        p95 = percentil_95(t)
        filas.append(
            {
                "consulta": nombre,
                "peticiones": len(t),
                "errores": errores.get(nombre, 0),
                "mediana_s": round(statistics.median(t), 3),
                "p95_s": round(p95, 3),
                "max_s": round(t[-1], 3),
            }
        )
    todos = sorted(x for v in tiempos.values() for x in v)
    total = {
        "peticiones": len(todos),
        "por_segundo": round(len(todos) / segundos, 1),
        "p95_s": round(percentil_95(todos), 3),
        "cumple": all(f["p95_s"] <= 2 and not f["errores"] for f in filas),
    }
    print(f"{'Consulta':32} {'n':>6} {'err':>4} {'mediana':>8} {'p95':>7} {'máx':>7}")
    for f in filas:
        print(
            f"{f['consulta']:32} {f['peticiones']:>6} {f['errores']:>4} {f['mediana_s']:>8.3f} "
            f"{f['p95_s']:>7.3f} {f['max_s']:>7.3f}"
        )
    print(
        f"Total: {total['peticiones']} peticiones ({total['por_segundo']}/s), p95 global {total['p95_s']} s · "
        f"{'CUMPLE' if total['cumple'] else 'NO CUMPLE'} RNF-03 (p95 ≤ 2 s sin errores)"
    )
    if lentas:
        print(f"Peticiones de más de 2 s: {len(lentas)}; empezaron en los segundos "
              f"{sorted({x[0] for x in lentas})[:10]}")
    return {"filas": filas, "total": total, "lentas": lentas}


async def medir(url: str, segundos: int, usuarios: int):
    import httpx

    base = url.rstrip("/") + "/api/v1"
    hoy = datetime.now(timezone.utc).date()
    tiempos: dict[str, list[float]] = {}
    errores: dict[str, int] = {}
    lentas: list = []  # (segundo de la prueba en que empezó, duración, consulta) de las que pasan de 2 s

    async with httpx.AsyncClient(timeout=30, limits=httpx.Limits(max_connections=usuarios), trust_env=False) as c:

        async def token(correo):
            r = await c.post(base + "/auth/login", json={"correo": correo, "password": PASSWORD})
            r.raise_for_status()
            return {"Authorization": "Bearer " + r.json()["token"]}

        admin = await token("admin@reportaya.demo")
        residentes = [await token(f"{n}@reportaya.demo") for n in ("residente", "carlos", "ana")]
        conserje = await token("mantenimiento@reportaya.demo")
        cats = (await c.get(base + "/categories", headers=admin)).json()
        folios = [r["folio"] for r in (await c.get(base + "/reports?pageSize=100", headers=admin)).json()["items"]]

        def escenarios(rnd):
            cat = rnd.choice(cats)["id"]
            desde = hoy - timedelta(days=rnd.randint(30, 900))
            return [
                ("RF-10 lista del residente", rnd.choice(residentes), "/reports?pageSize=20", {}),
                ("RF-10 detalle del residente", rnd.choice(residentes), None, {}),
                (
                    "RF-12 búsqueda",
                    admin,
                    f"/reports?categoriaId={cat}&avisoDesde={desde}&avisoHasta={hoy}&pageSize=20",
                    {},
                ),
                (
                    "RF-12 búsqueda por texto",
                    admin,
                    "/reports?texto=" + rnd.choice(["gotea", "lámpara", "drenaje"]) + "&pageSize=20",
                    {},
                ),
                ("RF-12 detalle e historial", admin, f"/reports/{rnd.choice(folios)}/history?pageSize=100", {}),
                (
                    "RF-13 tablero",
                    admin,
                    f"/metrics?desde={hoy - timedelta(days=rnd.choice([30, 90, 365]))}&hasta={hoy}",
                    {},
                ),
                ("RF-16 lista de Mantenimiento", conserje, "/reports?pageSize=20", {}),
            ]

        fin = time.monotonic() + segundos
        inicio_prueba = time.perf_counter()

        async def usuario(n):
            rnd = random.Random(n)
            propios = {}
            while time.monotonic() < fin:
                nombre, h, ruta, _ = rnd.choice(escenarios(rnd))
                if ruta is None:  # detalle de un reporte visible para ese residente
                    clave = h["Authorization"]
                    if clave not in propios:
                        propios[clave] = [
                            x["folio"] for x in (await c.get(base + "/reports?pageSize=50", headers=h)).json()["items"]
                        ]
                    ruta = f"/reports/{rnd.choice(propios[clave])}"
                t = time.perf_counter()
                r = await c.get(base + ruta, headers=h)
                tiempos.setdefault(nombre, []).append(time.perf_counter() - t)
                if time.perf_counter() - t > 2:
                    lentas.append((round(t - inicio_prueba, 1), round(time.perf_counter() - t, 1), nombre))
                if r.status_code != 200:
                    errores[nombre] = errores.get(nombre, 0) + 1

        await asyncio.gather(*(usuario(n) for n in range(usuarios)))

    return _resumen(tiempos, errores, lentas, segundos)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="accion", required=True)
    pr = sub.add_parser("preparar")
    pr.add_argument("--continuar", action="store_true", help="sigue una generación interrumpida sin borrar la base")
    m = sub.add_parser("medir")
    m.add_argument("--url", default="http://127.0.0.1:8000")
    m.add_argument("--segundos", type=int, default=60)
    m.add_argument("--usuarios", type=int, default=20)
    m.add_argument("--json", help="guarda el resultado en este archivo")
    a = ap.parse_args()
    if a.accion == "preparar":
        preparar(a.continuar)
    else:
        res = asyncio.run(medir(a.url, a.segundos, a.usuarios))
        if a.json:
            Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(0 if res["total"]["cumple"] else 1)
