"""Tablero de tiempos, incidencias recurrentes y adopción (RF-13) y su exportación a PDF (RF-23).

Un solo cálculo (`calcular_tablero`) alimenta la pantalla y el PDF, para que las cifras coincidan (RNF-16).
Todos los tiempos se miden desde la fecha de aviso; los objetivos y la ventana de recurrencia salen de los
parámetros (RF-27). `Cancelado` y `Unido` no cuentan en promedios, cumplimiento, recurrencia ni adopción.
"""

import io
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from .. import config, reloj
from ..db import get_db
from ..reglas import parametro
from ..util import day_end_utc, day_start_utc, responder, validacion
from .reportes import MOTIVO_LEGIBLE

router = APIRouter()
PRIORIDADES = ("Urgente", "Normal", "Menor")
EXCLUIDOS = ("Cancelado", "Unido")


def _redondear(x: float) -> int:
    """Porcentaje redondeado al entero (0.5 hacia arriba, no el redondeo bancario de Python)."""
    return int(x + 0.5)


def _hito(db, folio: str, estado: str) -> Optional[datetime]:
    """Primera vez que el reporte pasó a `estado` (tiempo de primera atención: EnProceso; de resolución: Terminado)."""
    f = db.execute(
        """SELECT MIN(e.fecha) AS f FROM entrada_historial e JOIN cambio_estado c ON c.entrada_id = e.id
                      WHERE e.reporte_folio = ? AND c.estado_nuevo = ?""",
        (folio, estado),
    ).fetchone()
    return reloj.de_texto(f["f"]) if f["f"] else None


def _bloque(db, r) -> str:
    """Personal propio o proveedores externos (RD-02, RF-13-AC-7). Un reporte sin responsable todavía es
    responsabilidad del personal del condominio."""
    if r["responsable_proveedor_id"]:
        return "proveedoresExternos"
    if r["responsable_usuario_id"]:
        m = db.execute(
            "SELECT tipo FROM usuario_mantenimiento WHERE usuario_id=?", (r["responsable_usuario_id"],)
        ).fetchone()
        if m and m["tipo"] == "ProveedorExterno":
            return "proveedoresExternos"
    return "personalPropio"


def _evaluar(aviso: datetime, hito: Optional[datetime], horas_objetivo: float, ahora: datetime) -> Optional[bool]:
    """True cumple, False incumple, None fuera del cálculo (objetivo aún no vence y no hay hito)."""
    limite = aviso + timedelta(hours=horas_objetivo)
    if hito is not None:
        return hito <= limite
    return False if ahora > limite else None


def _cumplimiento(resultados: list) -> dict:
    medidos = [x for x in resultados if x is not None]
    cumplen = sum(1 for x in medidos if x)
    return {
        "reportes": len(medidos),
        "cumplen": cumplen,
        "porcentaje": _redondear(100 * cumplen / len(medidos)) if medidos else None,
    }


def calcular_tablero(db, desde: date, hasta: date) -> dict:
    ahora = reloj.ahora()
    filas = db.execute(
        """SELECT r.*, c.nombre AS categoria FROM reporte r JOIN categoria c ON c.id = r.categoria_id
                          WHERE r.fecha_aviso BETWEEN ? AND ? ORDER BY r.fecha_aviso, r.folio""",
        (day_start_utc(desde), day_end_utc(hasta)),
    ).fetchall()
    por_estado: dict = defaultdict(int)
    por_categoria: dict = defaultdict(int)
    for r in filas:
        por_estado[r["estado"]] += 1
        por_categoria[r["categoria"]] += 1
    validos = [r for r in filas if r["estado"] not in EXCLUIDOS]

    objetivos_resolucion = {p: parametro(db, f"objetivoResolucion{p}Horas") for p in PRIORIDADES}
    objetivo_primera = parametro(db, "objetivoPrimeraAtencionUrgenteHoras")
    acumulado = {
        p: {"primera": [], "resolucion": [], "cumplePrimera": defaultdict(list), "cumpleResolucion": defaultdict(list)}
        for p in PRIORIDADES
    }
    for r in validos:
        p = r["prioridad"] or r["prioridad_sugerida"]
        aviso = reloj.de_texto(r["fecha_aviso"])
        primera, resolucion = _hito(db, r["folio"], "EnProceso"), _hito(db, r["folio"], "Terminado")
        a = acumulado[p]
        if primera:
            a["primera"].append((primera - aviso).total_seconds() / 60)
        if resolucion:
            a["resolucion"].append((resolucion - aviso).total_seconds() / 3600)
        bloque = _bloque(db, r)
        if p == "Urgente":  # Normal y Menor no tienen objetivo de primera atención (RD-02)
            a["cumplePrimera"][bloque].append(_evaluar(aviso, primera, objetivo_primera, ahora))
        a["cumpleResolucion"][bloque].append(_evaluar(aviso, resolucion, objetivos_resolucion[p], ahora))

    por_prioridad = []
    for p in PRIORIDADES:
        a = acumulado[p]
        item = {
            "prioridad": p,
            "primeraAtencionPromedioMin": round(sum(a["primera"]) / len(a["primera"]), 1) if a["primera"] else None,
            "resolucionPromedioHoras": round(sum(a["resolucion"]) / len(a["resolucion"]), 1)
            if a["resolucion"]
            else None,
            "cumplimientoResolucion": {
                b: _cumplimiento(a["cumpleResolucion"][b]) for b in ("personalPropio", "proveedoresExternos")
            },
        }
        if p == "Urgente":
            item["cumplimientoPrimeraAtencion"] = {
                b: _cumplimiento(a["cumplePrimera"][b]) for b in ("personalPropio", "proveedoresExternos")
            }
        por_prioridad.append(item)

    # Incidencias recurrentes (definición de 1.3): ventana contada desde la fecha de consulta, no desde el rango.
    hoy = ahora.astimezone(config.TIMEZONE).date()
    inicio_ventana = day_start_utc(hoy - timedelta(days=int(parametro(db, "ventanaRecurrenciaDias"))))
    minimo = int(parametro(db, "minimoRecurrencia"))
    grupos = db.execute(
        """SELECT c.nombre AS categoria, COALESCE(r.ubicacion_origen_id, r.ubicacion_id) AS origen,
                           GROUP_CONCAT(r.folio) AS folios, count(*) AS n
                           FROM reporte r JOIN categoria c ON c.id = r.categoria_id
                           WHERE r.estado NOT IN ('Cancelado','Unido') AND r.fecha_aviso >= ? AND r.fecha_aviso <= ?
                           GROUP BY r.categoria_id, origen HAVING count(*) >= ? ORDER BY n DESC, categoria""",
        (inicio_ventana, reloj.a_texto(ahora), minimo),
    ).fetchall()
    recurrentes = [
        {
            "categoria": g["categoria"],
            "ubicacionOrigen": db.execute("SELECT etiqueta FROM v_ubicacion WHERE id=?", (g["origen"],)).fetchone()[
                "etiqueta"
            ],
            "folios": sorted(g["folios"].split(",")),
        }
        for g in grupos
    ]

    detenciones = []
    for r in validos:
        holds = db.execute(
            "SELECT * FROM detencion WHERE reporte_folio=? ORDER BY fecha_inicio", (r["folio"],)
        ).fetchall()
        if holds:
            horas = (
                sum(
                    (
                        (reloj.de_texto(h["fecha_fin"]) if h["fecha_fin"] else ahora)
                        - reloj.de_texto(h["fecha_inicio"])
                    ).total_seconds()
                    for h in holds
                )
                / 3600
            )
            motivos = list(
                dict.fromkeys(h["texto_otro"] if h["motivo"] == "Otro" else MOTIVO_LEGIBLE[h["motivo"]] for h in holds)
            )
            detenciones.append({"folio": r["folio"], "horasDetenido": round(horas, 1), "motivos": motivos})

    reaperturas = sum(
        max(db.execute("SELECT count(*) FROM ciclo_atencion WHERE reporte_folio=?", (r["folio"],)).fetchone()[0] - 1, 0)
        for r in validos
    )
    sistema = sum(1 for r in validos if r["medio_origen"] == "Sistema")
    return {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "porEstado": dict(por_estado),
        "porCategoria": dict(por_categoria),
        "porPrioridad": por_prioridad,
        "recurrentes": recurrentes,
        "detenciones": detenciones,
        "adopcionPorcentaje": _redondear(100 * sistema / len(validos)) if validos else None,
        "reaperturas": reaperturas,
    }


@router.get("/metrics")
def get_metrics(request: Request, desde: date = Query(...), hasta: date = Query(...), db=Depends(get_db)):
    if hasta < desde:
        raise validacion("hasta", "La fecha final no puede ser anterior a la inicial")
    tablero = calcular_tablero(db, desde, hasta)
    if "application/pdf" in request.headers.get("accept", ""):
        return Response(
            pdf_del_tablero(tablero),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="tablero_{desde}_{hasta}.pdf"'},
        )
    return responder(tablero)


# ------------------------------------------------------------------ exportación (RF-23)
def _fmt(x, sufijo=""):
    return "—" if x is None else f"{x:g}{sufijo}"


def pdf_del_tablero(t: dict) -> bytes:
    """PDF imprimible con las mismas cifras que la pantalla (RF-23-AC-2, RNF-16)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    estilos = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Tablero ReportaYa")
    desde = date.fromisoformat(t["desde"]).strftime("%d/%m/%Y")
    hasta = date.fromisoformat(t["hasta"]).strftime("%d/%m/%Y")
    estilo_tabla = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]
    )

    def pct(b):
        return "—" if b.get("porcentaje") is None else f"{b['porcentaje']} % ({b['cumplen']} de {b['reportes']})"

    partes = [
        Paragraph("ReportaYa · Tablero de mantenimiento", estilos["Title"]),
        Paragraph(f"Periodo de aviso: {desde} al {hasta}", estilos["Normal"]),
        Spacer(1, 12),
        Paragraph("Tiempos y cumplimiento por prioridad", estilos["Heading2"]),
    ]
    filas = [
        [
            "Prioridad",
            "1.ª atención prom.",
            "Resolución prom.",
            "Cumpl. 1.ª atención (propio / externos)",
            "Cumpl. resolución (propio / externos)",
        ]
    ]
    for p in t["porPrioridad"]:
        cp = p.get("cumplimientoPrimeraAtencion")
        cr = p["cumplimientoResolucion"]
        filas.append(
            [
                p["prioridad"],
                _fmt(p["primeraAtencionPromedioMin"], " min"),
                _fmt(p["resolucionPromedioHoras"], " h"),
                f"{pct(cp['personalPropio'])} / {pct(cp['proveedoresExternos'])}" if cp else "Sin objetivo",
                f"{pct(cr['personalPropio'])} / {pct(cr['proveedoresExternos'])}",
            ]
        )
    partes += [
        Table(filas, style=estilo_tabla),
        Spacer(1, 12),
        Paragraph("Incidencias recurrentes", estilos["Heading2"]),
    ]
    if t["recurrentes"]:
        partes.append(
            Table(
                [["Categoría", "Ubicación de origen", "Folios"]]
                + [[x["categoria"], x["ubicacionOrigen"], ", ".join(x["folios"])] for x in t["recurrentes"]],
                style=estilo_tabla,
            )
        )
    else:
        partes.append(Paragraph("No hay incidencias recurrentes.", estilos["Normal"]))
    partes += [
        Spacer(1, 12),
        Paragraph("Adopción y reaperturas", estilos["Heading2"]),
        Paragraph(f"Adopción (reportes con medio «Sistema»): {_fmt(t['adopcionPorcentaje'], ' %')}", estilos["Normal"]),
        Paragraph(f"Reaperturas: {t['reaperturas']}", estilos["Normal"]),
    ]
    if t["detenciones"]:
        partes += [
            Spacer(1, 12),
            Paragraph("Tiempo detenido", estilos["Heading2"]),
            Table(
                [["Folio", "Horas detenido", "Motivos"]]
                + [[d["folio"], _fmt(d["horasDetenido"]), ", ".join(d["motivos"])] for d in t["detenciones"]],
                style=estilo_tabla,
            ),
        ]
    doc.build(partes)
    return buf.getvalue()
