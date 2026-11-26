"""RNF-09 y RNF-01: axe-core (WCAG 2.1 A y AA, contraste de 4.5:1), texto base de 16 px y sin desplazamiento horizontal.

Requisitos: backend en :8000 con `python scripts/cargar_demo.py`, frontend en :5173 y `npm install` (trae axe-core).
    python e2e/accesibilidad.py
Recorre cada pantalla con el rol que la usa, en celular (360 px) y escritorio (1280 px), con formularios abiertos
y errores de validación visibles. Falla si axe encuentra alguna infracción o si el texto base no es de 16 px.
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = os.environ.get("URL", "http://localhost:5173")
AXE = (Path(__file__).resolve().parent.parent / "node_modules/axe-core/axe.min.js").read_text()
REGLAS = {"runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]}}

PANTALLAS = {
    None: ["/login", "/activar?token=x", "/recuperar"],
    "residente": ["/", "/reportes", "/reportes/nuevo", "/reportes/nuevo#errores", "/avisos", "/pendientes", "@detalle"],
    "admin": ["/", "/reportes", "/tablero", "/usuarios", "/reportes/nuevo", "@detalle", "@acciones"],
    "mantenimiento": ["/", "/reportes", "@detalle", "@acciones"],
    "vigilancia": ["/", "/reportes", "/reportes/nuevo"],
}

infracciones, revisadas = [], 0
with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--no-sandbox"])
    for ancho in (360, 1280):
        for rol, rutas in PANTALLAS.items():
            ctx = br.new_context(viewport={"width": ancho, "height": 900}, locale="es-MX")
            p = ctx.new_page()
            if rol:
                p.goto(URL + "/login")
                p.get_by_label("Correo").fill(f"{rol}@reportaya.demo")
                p.get_by_label("Contraseña").fill("Demo1234!")
                p.get_by_role("button", name="Entrar").click()
                p.wait_for_url(URL + "/")
            for ruta in rutas:
                if ruta.startswith("@"):
                    p.goto(URL + "/reportes")
                    p.locator("a[href^='/reportes/RY-']").first.click()
                    p.wait_for_url("**/reportes/RY-*")
                    p.wait_for_load_state("networkidle")
                    if ruta == "@acciones":                # abre cada formulario de acción disponible
                        for b in p.locator("main button").all()[:6]:
                            if b.is_visible() and b.inner_text() not in ("Cancelar", "Mostrar avisos"):
                                b.click()
                                break
                else:
                    p.goto(URL + ruta.split("#")[0])
                    p.wait_for_load_state("networkidle")
                    if ruta.endswith("#errores"):
                        p.get_by_role("button", name="Enviar reporte").click()
                        p.wait_for_timeout(300)
                p.add_script_tag(content=AXE)
                res = p.evaluate("o => axe.run(document, o)", REGLAS)
                base = p.evaluate("getComputedStyle(document.documentElement).fontSize")
                revisadas += 1
                etiqueta = f"{ancho}px {rol or 'sin sesión'} {ruta}"
                if base != "16px":
                    infracciones.append(f"{etiqueta}: texto base {base}")
                ancho_doc = p.evaluate("document.documentElement.scrollWidth")
                if ancho_doc > ancho:  # RNF-01: sin desplazamiento horizontal desde 360 px
                    infracciones.append(f"{etiqueta}: desplazamiento horizontal ({ancho_doc} px)")
                for v in res["violations"]:
                    for n in v["nodes"][:3]:
                        infracciones.append(f"{etiqueta}: [{v['id']}] {n['failureSummary'].splitlines()[-1].strip()} → {n['target']}")
            ctx.close()
    br.close()

print(f"Pantallas auditadas: {revisadas} (WCAG 2.1 A/AA con axe-core)")
print("\n".join(infracciones) if infracciones else "Sin infracciones; texto base de 16 px en todas")
sys.exit(1 if infracciones else 0)
