"""E2E del modo sin conexión (RNF-11) sobre la versión compilada con service worker.

Requisitos: backend en :8000 con `python scripts/cargar_demo.py` recién ejecutado y
`npm run build && npm run preview -- --port 4173` en frontend/.
    URL=http://localhost:4173 python e2e/sin_conexion.py

Comprueba que, sin señal: la app abre desde caché, la lista guardada se muestra con aviso, un reporte nuevo
queda «Pendiente» en el dispositivo y, al volver la señal, se envía una sola vez («Enviado» con folio).
"""
import os
import re
import struct
import sys
import zlib

from playwright.sync_api import expect, sync_playwright

URL = os.environ.get("URL", "http://localhost:4173")
OUT = os.environ.get("CAPTURAS", "capturas")
os.makedirs(OUT, exist_ok=True)
FOTO = "/tmp/foto_sin_conexion.png"
fila = b"\x00" + bytes((60, 120, 200)) * 160


def b(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)


open(FOTO, "wb").write(b"\x89PNG\r\n\x1a\n" + b(b"IHDR", struct.pack(">IIBBBBB", 160, 120, 8, 2, 0, 0, 0))
                       + b(b"IDAT", zlib.compress(fila * 120)) + b(b"IEND", b""))
errores = []
DESCRIPCION = "Se fundió el foco del pasillo del tercer piso, capturado sin señal"

with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": 390, "height": 860}, locale="es-MX", timezone_id="America/Mexico_City")
    p = ctx.new_page()
    p.on("pageerror", lambda e: errores.append(f"pageerror {e}"))
    p.goto(URL + "/login")
    p.get_by_label("Correo").fill("residente@reportaya.demo")
    p.get_by_label("Contraseña").fill("Demo1234!")
    p.get_by_role("button", name="Entrar").click()
    p.wait_for_url(URL + "/")
    p.evaluate("navigator.serviceWorker.ready")              # el SW queda activo y con la app en caché
    # Con señal: se visitan la lista y el formulario (catálogos), que quedan guardados.
    p.goto(URL + "/reportes")
    expect(p.get_by_text("RY-").first).to_be_visible()
    total_antes = p.locator("a[href^='/reportes/RY-']").count()
    p.goto(URL + "/reportes/nuevo")
    expect(p.get_by_label("Categoría")).to_be_visible()

    # Sin señal: recarga desde caché, lista guardada y alta encolada.
    ctx.set_offline(True)
    p.goto(URL + "/reportes")
    expect(p.get_by_text("Sin conexión. Puedes consultar")).to_be_visible()
    expect(p.get_by_text("Sin conexión: lista guardada el")).to_be_visible()
    p.screenshot(path=f"{OUT}/16_sin_conexion_lista.png", full_page=True)
    p.goto(URL + "/reportes/nuevo")
    p.get_by_label("Categoría").select_option(label="Iluminación")
    p.get_by_label("Subtipo").select_option(label="Pasillo o área techada")
    p.get_by_label("Descripción").fill(DESCRIPCION)
    p.locator("input[name=peligro]").nth(1).check()
    p.locator("input[name=acceso]").first.check()
    p.locator("input[type=file]").first.set_input_files(FOTO)
    p.get_by_role("button", name="Enviar reporte").click()
    p.wait_for_url(URL + "/pendientes")
    expect(p.get_by_text("Pendiente", exact=True)).to_be_visible()
    expect(p.get_by_text("1 sin enviar")).to_be_visible()
    p.screenshot(path=f"{OUT}/17_sin_conexion_pendiente.png", full_page=True)

    # Vuelve la señal: se envía solo, una vez, y aparece el folio.
    ctx.set_offline(False)
    p.evaluate("window.dispatchEvent(new Event('online'))")
    expect(p.get_by_text("Enviado", exact=True)).to_be_visible(timeout=15000)
    folio = p.locator("a[href^='/reportes/RY-']").first.inner_text()
    assert re.fullmatch(r"RY-\d{6}", folio), folio
    p.get_by_role("button", name="Reintentar ahora").click()      # reintento extra: no debe duplicar
    p.wait_for_timeout(1500)
    p.screenshot(path=f"{OUT}/18_sin_conexion_enviado.png", full_page=True)
    p.goto(URL + "/reportes")
    expect(p.get_by_text(folio)).to_be_visible()
    total_despues = p.locator("a[href^='/reportes/RY-']").count()
    iguales = p.get_by_text(DESCRIPCION[:40]).count()
    ctx.close()

    # Mantenimiento consulta sin señal el detalle de un asignado que ya abrió (última frase de RNF-11).
    ctx = br.new_context(viewport={"width": 390, "height": 860}, locale="es-MX", timezone_id="America/Mexico_City")
    p = ctx.new_page()
    p.on("pageerror", lambda e: errores.append(f"pageerror {e}"))
    p.goto(URL + "/login")
    p.get_by_label("Correo").fill("mantenimiento@reportaya.demo")
    p.get_by_label("Contraseña").fill("Demo1234!")
    p.get_by_role("button", name="Entrar").click()
    p.wait_for_url(URL + "/")
    p.evaluate("navigator.serviceWorker.ready")
    p.goto(URL + "/reportes")
    p.locator("a[href^='/reportes/RY-']").first.click()
    p.wait_for_url(re.compile(r".*/reportes/RY-\d{6}$"))
    asignado = p.url.rsplit("/", 1)[1]
    p.wait_for_load_state("networkidle")
    ctx.set_offline(True)
    p.reload()
    expect(p.get_by_text("Información guardada el")).to_be_visible()
    expect(p.get_by_role("heading", name=asignado)).to_be_visible()
    p.screenshot(path=f"{OUT}/19_sin_conexion_mantenimiento.png", full_page=True)
    br.close()

print("antes", total_antes, "después", total_despues, "copias", iguales, "folio", folio)
if errores:
    print("\n".join(errores))
    sys.exit(1)
assert total_despues == total_antes + 1, "el reporte encolado debía crearse exactamente una vez"
print(f"OK sin conexión (Mantenimiento consultó {asignado} sin señal)")
