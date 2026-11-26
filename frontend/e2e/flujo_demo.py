"""Recorrido E2E de la demo (S11-A1): Residente, Administración, Mantenimiento y Vigilancia en Chrome con Playwright.

Requisitos: backend en :8000 con `python scripts/cargar_demo.py` recién ejecutado y frontend en :5173 (`npm run dev`).
    pip install playwright && python -m playwright install chromium
    CAPTURAS=../docs/capturas python e2e/flujo_demo.py
Guarda una captura por paso en CAPTURAS y falla si algún paso no se cumple.
"""
import sys, re
from playwright.sync_api import sync_playwright, expect
URL = "http://localhost:5173"
import os
OUT = os.environ.get("CAPTURAS", "capturas")
os.makedirs(OUT, exist_ok=True)
errores = []
FOTO = os.path.join(OUT, "foto_prueba.png")

def png():
    import struct, zlib
    fila = b"\x00" + bytes((200, 60, 60)) * 160
    def b(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(FOTO, "wb").write(b"\x89PNG\r\n\x1a\n" + b(b"IHDR", struct.pack(">IIBBBBB", 160, 120, 8, 2, 0, 0, 0)) + b(b"IDAT", zlib.compress(fila * 120)) + b(b"IEND", b""))
png()

def sesion(browser, correo, ancho=1280):
    ctx = browser.new_context(viewport={"width": ancho, "height": 900}, locale="es-MX", timezone_id="America/Mexico_City")
    p = ctx.new_page()
    p.on("console", lambda m: m.type == "error" and errores.append(f"[{correo}] {m.text}"))
    p.on("pageerror", lambda e: errores.append(f"[{correo}] pageerror {e}"))
    p.goto(URL + "/login")
    p.get_by_label("Correo").fill(correo)
    p.get_by_label("Contraseña").fill("Demo1234!")
    p.get_by_role("button", name="Entrar").click()
    p.wait_for_url(URL + "/")
    return ctx, p

def foto(p, nombre):
    p.screenshot(path=f"{OUT}/{nombre}.png", full_page=True)

with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--no-sandbox"])

    # 1. Residente (celular 390 px): alta con error de validación y luego correcta
    ctx, p = sesion(br, "residente@reportaya.demo", ancho=390)
    foto(p, "01_inicio_residente")
    p.goto(URL + "/reportes/nuevo")
    p.get_by_label("Categoría").select_option(label="Plomería y fugas")
    p.get_by_label("Subtipo").select_option(label="Fuga activa")
    p.get_by_label("Descripción").fill("Gotea")
    p.locator("input[name=peligro]").nth(1).check()
    p.locator("input[name=acceso]").first.check()
    p.locator("input[type=file]").first.set_input_files(FOTO)
    p.get_by_role("button", name="Enviar reporte").click()
    expect(p.get_by_text("La descripción debe tener entre 10 y 1,000 caracteres").first).to_be_visible()
    assert p.get_by_label("Descripción").input_value() == "Gotea", "RF-03-AC-5: se perdieron los datos"
    foto(p, "02_error_validacion")
    p.get_by_label("Descripción").fill("Gotea agua del techo del baño cuando usan la regadera arriba")
    p.get_by_role("button", name="Enviar reporte").click()
    p.wait_for_url(re.compile(r".*/reportes/RY-\d{6}$"))
    folio = p.url.rsplit("/", 1)[1]
    expect(p.get_by_text("Reporte registrado.")).to_be_visible()
    foto(p, "03_reporte_creado_residente")
    print("folio nuevo:", folio)

    # 2. Administración: lista con búsqueda, asignar
    actx, a = sesion(br, "admin@reportaya.demo")
    a.goto(URL + "/reportes"); a.wait_for_selector("text=reporte(s)")
    foto(a, "04_lista_admin")
    a.get_by_label("Texto en la descripción").fill("regadera"); a.get_by_role("button", name="Buscar").click()
    expect(a.get_by_text(folio)).to_be_visible()
    a.get_by_text(folio).click()
    a.get_by_role("button", name="Asignar").click()
    a.get_by_label("Prioridad").select_option("Urgente")
    a.locator("select:has(option:has-text('Ramón Torres'))").select_option(label="Ramón Torres · Conserje")
    a.get_by_role("button", name="Asignar").last.click()
    expect(a.get_by_text("Asignar: listo.")).to_be_visible()
    expect(a.get_by_text("Asignado", exact=True).first).to_be_visible()
    foto(a, "05_asignado_admin")

    # 3. Mantenimiento: sus asignados, iniciar, terminar sin foto (error) y con foto
    mctx, m = sesion(br, "mantenimiento@reportaya.demo", ancho=390)
    m.goto(URL + "/reportes"); m.wait_for_selector("text=reporte(s)")
    foto(m, "06_asignados_mantenimiento")
    m.get_by_text(folio).click()
    m.get_by_role("button", name="Iniciar atención").click(); m.get_by_role("button", name="Iniciar", exact=True).click()
    expect(m.get_by_text("Iniciar atención: listo.")).to_be_visible()
    m.get_by_role("button", name="Marcar terminado").click(); m.get_by_role("button", name="Terminar", exact=True).click()
    expect(m.get_by_text("Adjunte al menos una foto del trabajo terminado")).to_be_visible()
    foto(m, "07_error_terminar_sin_foto")
    m.locator("form input[type=file]").set_input_files(FOTO)
    m.get_by_label("Nota del trabajo (opcional)").fill("Se resanó la tubería del piso de arriba")
    m.get_by_role("button", name="Terminar", exact=True).click()
    expect(m.get_by_text("Marcar terminado: listo.")).to_be_visible()
    foto(m, "08_terminado_mantenimiento")

    # 4. Residente confirma
    p.goto(URL + f"/reportes/{folio}")
    expect(p.get_by_text("¿Quedó bien la reparación?")).to_be_visible()
    p.get_by_role("button", name="Enviar respuesta").click()
    expect(p.get_by_text("listo.")).to_be_visible()
    foto(p, "09_confirmado_residente")
    assert p.get_by_text("Notas internas").count() == 0 and p.get_by_text("Propietario").count() == 0

    # 5. Administración cierra; tablero; avisos; usuarios
    a.goto(URL + f"/reportes/{folio}")
    a.get_by_role("button", name="Cerrar", exact=True).click(); a.get_by_role("button", name="Cerrar reporte").click()
    expect(a.get_by_text("Cerrar: listo.")).to_be_visible()
    a.get_by_role("button", name="Ver historial").click(); a.wait_for_timeout(500)
    foto(a, "10_cerrado_con_historial")
    a.goto(URL + "/tablero"); a.wait_for_selector("text=Tiempos y cumplimiento")
    a.get_by_label("Aviso desde").fill("2026-09-01"); a.get_by_role("button", name="Consultar").click(); a.wait_for_timeout(700)
    foto(a, "11_tablero")
    with a.expect_download() as d:
        a.get_by_role("button", name="Exportar PDF").click()
    d.value.save_as(f"{OUT}/tablero.pdf")
    a.goto(URL + "/avisos"); a.wait_for_selector("text=Mis avisos"); foto(a, "12_avisos_admin")
    a.goto(URL + "/usuarios"); a.wait_for_selector("text=Cuentas")
    a.get_by_label("Nombre").fill("Lucía Fernández"); a.get_by_label("Correo").fill("lucia@ejemplo.mx")
    a.get_by_label("Departamento").select_option(label="B-301")
    a.get_by_role("button", name="Crear cuenta y enviar enlace").click()
    expect(a.get_by_text("se le envió el enlace de activación")).to_be_visible()
    foto(a, "13_usuarios")

    # 6. Vigilancia: no ve el reporte de la residente (404)
    vctx, v = sesion(br, "vigilancia@reportaya.demo")
    v.goto(URL + f"/reportes/{folio}"); expect(v.get_by_text("No se pudo abrir el reporte")).to_be_visible()
    foto(v, "14_vigilancia_404")
    v.goto(URL + "/reportes"); v.wait_for_selector("text=reporte(s)"); foto(v, "15_lista_vigilancia")
    br.close()

print("ERRORES DE CONSOLA:", errores or "ninguno")
