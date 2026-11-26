"""RNF-04: una foto de 10 MB se sube en 15 s o menos con la red limitada a 10 Mbit/s (verificación con el navegador).

Requisitos: backend en :8000 con `python scripts/cargar_demo.py` y frontend en :5173 (`npm run dev`).
    python e2e/subida_10mb.py
Limita la red de Chrome por CDP (10 Mbit/s de subida y de bajada, 40 ms de latencia), adjunta una foto JPEG
de 10 MB (el máximo permitido) en «Nuevo reporte» y mide desde «Enviar reporte» hasta ver el folio creado.
"""
import os
import random
import re
import sys
import time

from PIL import Image
from playwright.sync_api import expect, sync_playwright

URL = os.environ.get("URL", "http://localhost:5173")
FOTO = "/tmp/foto_10mb.jpg"
LIMITE = 10 * 1024 * 1024
MBIT = 10

# JPEG real de casi 10 MB: ruido (no se comprime) con la calidad que da el tamaño más cercano al límite.
lado = 2900
img = Image.frombytes("RGB", (lado, lado), random.Random(4).randbytes(lado * lado * 3))
for calidad in range(100, 60, -1):
    img.save(FOTO, "JPEG", quality=calidad)
    if os.path.getsize(FOTO) <= LIMITE:
        break
tam = os.path.getsize(FOTO)
print(f"Foto: {tam / 1024 / 1024:.2f} MiB ({tam:,} bytes)")

with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--no-sandbox"])
    ctx = br.new_context(viewport={"width": 390, "height": 860}, locale="es-MX")
    p = ctx.new_page()
    p.goto(URL + "/login")
    p.get_by_label("Correo").fill("residente@reportaya.demo")
    p.get_by_label("Contraseña").fill("Demo1234!")
    p.get_by_role("button", name="Entrar").click()
    p.wait_for_url(URL + "/")
    p.goto(URL + "/reportes/nuevo")
    p.get_by_label("Categoría").select_option(label="Plomería y fugas")
    p.get_by_label("Subtipo").select_option(label="Fuga activa")
    p.get_by_label("Descripción").fill("Prueba de subida de una foto de 10 MB con la red limitada")
    p.locator("input[name=peligro]").nth(1).check()
    p.locator("input[name=acceso]").first.check()
    p.locator("input[type=file]").first.set_input_files(FOTO)

    cdp = ctx.new_cdp_session(p)
    bps = MBIT * 1_000_000 / 8
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 40,
                                                  "downloadThroughput": bps, "uploadThroughput": bps})
    t = time.perf_counter()
    p.get_by_role("button", name="Enviar reporte").click()
    p.wait_for_url(re.compile(r".*/reportes/RY-\d{6}$"), timeout=120000)
    expect(p.get_by_text("Reporte registrado.")).to_be_visible()
    segundos = time.perf_counter() - t
    rechazados = p.get_by_text("Algunos archivos no se guardaron").count()
    folio = p.url.rsplit("/", 1)[1]
    br.close()

teorico = tam * 8 / (MBIT * 1_000_000)
print(f"Folio {folio}: subida y registro en {segundos:.1f} s con {MBIT} Mbit/s (mínimo teórico {teorico:.1f} s)")
if rechazados:
    sys.exit("La foto fue rechazada")
print("CUMPLE RNF-04 (≤ 15 s)" if segundos <= 15 else "NO CUMPLE RNF-04")
sys.exit(0 if segundos <= 15 else 1)
