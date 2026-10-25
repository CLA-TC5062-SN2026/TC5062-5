"""Reportes y sus subrecursos (RF-03, RF-04, RF-12, RF-17, RF-18, RF-20, RF-23).

Alcance de esta entrega: CRUD. Las transiciones de estado (assignments, cycles, completions, closures,
reopenings, cancellations, merges), los archivos descargables, resident-responses, warranty y metrics
quedan para la actividad de reglas de negocio / seguridad.
"""
import json
import re
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, File, Form, Header, Path, Query, Response, UploadFile
from typing import Literal
from datetime import date

from .. import config, schemas as S
from ..db import get_db, tx
from ..serial import (COST_SQL, NOTE_SQL, cost_out, hold_out, note_out, report_detail, report_summary, ubicacion_out, b)
from ..util import (FOLIO_RE, actor, conflicto, day_end_utc, day_start_utc, new_id, no_encontrado, now_utc, out_dt,
                    paginacion, prohibido, responder, to_utc, validacion, verificar_if_match, peticion_invalida)

router = APIRouter()
FolioP = Path(..., pattern=FOLIO_RE)
ABIERTOS = ("Asignado", "EnProceso")


def _reporte(db, folio):
    r = db.execute("SELECT * FROM reporte WHERE folio=?", (folio,)).fetchone()
    if not r:
        raise no_encontrado("Reporte no encontrado")
    return r


def _historial(db, folio, autor_id, tipo, campo=None, anterior=None, nuevo=None, comentario=None):
    eid = new_id()
    db.execute("""INSERT INTO entrada_historial (id, reporte_folio, fecha, tipo, campo, valor_anterior, valor_nuevo,
                  comentario, autor_id) VALUES (?,?,?,?,?,?,?,?,?)""",
               (eid, folio, now_utc(), tipo, campo, anterior, nuevo, comentario, autor_id))
    return eid


# ------------------------------------------------------------------ validaciones compartidas
def _resolver_categoria(db, categoria_id, subtipo):
    cat = db.execute("SELECT * FROM categoria WHERE id=?", (categoria_id,)).fetchone()
    if not cat:
        raise validacion("categoriaId", "La categoría no existe")
    subs = db.execute("SELECT nombre, prioridad_sugerida FROM subtipo WHERE categoria_id=?", (categoria_id,)).fetchall()
    if subs and subtipo is None:
        raise validacion("subtipo", "La categoría exige un subtipo")
    if not subs and subtipo is not None:
        raise validacion("subtipo", "La categoría no define subtipos")
    if subs:
        s = next((x for x in subs if x["nombre"].lower() == subtipo.strip().lower()), None)
        if not s:
            raise validacion("subtipo", "El subtipo no pertenece a la categoría")
        return cat, s["nombre"], s["prioridad_sugerida"]
    return cat, None, cat["prioridad_sugerida"]


def _resolver_ubicacion(db, u: S.Ubicacion, campo="ubicacion"):
    if u.tipo == "Unidad":
        if not u.unidadId or u.areaComunId:
            raise validacion(f"{campo}.unidadId", "Una ubicación de tipo Unidad requiere unidadId (y no areaComunId)")
        if u.referencia:
            raise validacion(f"{campo}.referencia", "La referencia aplica solo a áreas comunes (RD-13)")
        existe = db.execute("SELECT b.activa FROM unidad x JOIN ubicacion b ON b.id=x.ubicacion_id WHERE x.ubicacion_id=?", (u.unidadId,)).fetchone()
        uid, parte, ref = u.unidadId, u.parteAfectada, None
    else:
        if not u.areaComunId or u.unidadId:
            raise validacion(f"{campo}.areaComunId", "Una ubicación de tipo AreaComun requiere areaComunId (y no unidadId)")
        if u.parteAfectada:
            raise validacion(f"{campo}.parteAfectada", "La parte afectada aplica solo a unidades (RD-13)")
        existe = db.execute("SELECT b.activa FROM area_comun x JOIN ubicacion b ON b.id=x.ubicacion_id WHERE x.ubicacion_id=?", (u.areaComunId,)).fetchone()
        uid, parte, ref = u.areaComunId, None, u.referencia
    if not existe:
        raise validacion(f"{campo}.{'unidadId' if u.tipo == 'Unidad' else 'areaComunId'}", "La ubicación no existe")
    if not existe["activa"]:
        raise validacion(campo, "La ubicación está desactivada")
    for nombre, v in (("parteAfectada", parte), ("referencia", ref)):
        if v is not None and len(v) > 200:
            raise validacion(f"{campo}.{nombre}", "Máximo 200 caracteres")
    return uid, (parte.strip() if parte else None), (ref.strip() if ref else None)


def _descripcion(texto):
    if len(texto.strip()) < 10 or len(texto) > 1000:
        raise validacion("descripcion", "Debe tener entre 10 y 1000 caracteres")
    return texto.strip()


# ------------------------------------------------------------------ listado y búsqueda (RF-12)
@router.get("/reports")
def list_reports(ubicacionTipo: Optional[Literal["Unidad", "AreaComun"]] = None,
                 ubicacionId: Optional[str] = Query(None, pattern=r"^[0-9a-fA-F-]{36}$"),
                 categoriaId: Optional[str] = Query(None, pattern=r"^[0-9a-fA-F-]{36}$"),
                 estado: Optional[Literal["Reportado", "Asignado", "EnProceso", "Terminado", "Cerrado", "Cancelado", "Unido"]] = None,
                 prioridad: Optional[Literal["Urgente", "Normal", "Menor"]] = None,
                 responsableId: Optional[str] = Query(None, pattern=r"^[0-9a-fA-F-]{36}$"),
                 medioOrigen: Optional[S.MedioOrigen] = None,
                 avisoDesde: Optional[date] = None, avisoHasta: Optional[date] = None,
                 texto: Optional[str] = None, db=Depends(get_db), pg=Depends(paginacion)):
    w, p = [], []
    if ubicacionTipo:
        w.append("(SELECT tipo FROM ubicacion WHERE id=r.ubicacion_id)=?"); p.append(ubicacionTipo)
    if ubicacionId:
        w.append("(r.ubicacion_id=? OR r.ubicacion_origen_id=?)"); p += [ubicacionId, ubicacionId]
    if categoriaId:
        w.append("r.categoria_id=?"); p.append(categoriaId)
    if estado:
        w.append("r.estado=?"); p.append(estado)
    if prioridad:
        w.append("r.prioridad=?"); p.append(prioridad)
    if responsableId:
        w.append("(r.responsable_usuario_id=? OR r.responsable_proveedor_id=?)"); p += [responsableId, responsableId]
    if medioOrigen:
        w.append("r.medio_origen=?"); p.append(medioOrigen)
    if avisoDesde:
        w.append("r.fecha_aviso >= ?"); p.append(day_start_utc(avisoDesde))
    if avisoHasta:  # rangos inclusivos por días completos en la zona del condominio
        w.append("r.fecha_aviso <= ?"); p.append(day_end_utc(avisoHasta))
    if texto:
        esc = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        w.append("r.descripcion LIKE ? ESCAPE '\\'"); p.append(f"%{esc}%")
    page, size = pg
    sql_from = "FROM reporte r" + (" WHERE " + " AND ".join(w) if w else "")
    total = db.execute(f"SELECT count(*) {sql_from}", p).fetchone()[0]
    filas = db.execute(f"SELECT r.* {sql_from} ORDER BY r.fecha_aviso DESC, r.folio DESC LIMIT ? OFFSET ?",
                       p + [size, (page - 1) * size]).fetchall()
    return responder({"items": [report_summary(db, f) for f in filas],
                      "pagination": {"page": page, "pageSize": size, "total": total}})


# ------------------------------------------------------------------ alta (RF-03 / RF-04)
@router.post("/reports")
def create_report(datos: str = Form(...), fotos: list[UploadFile] = File(default=[]),
                  video: Optional[UploadFile] = File(default=None),
                  idempotency_key: Optional[str] = Header(default=None),  # aceptado; ver revision_sql.md
                  db=Depends(get_db), quien=Depends(actor)):
    try:
        d = S.parsear(S.ReportCreate, json.loads(datos))
    except json.JSONDecodeError:
        raise peticion_invalida("La parte `datos` no es un JSON válido")
    if len(fotos) > 5:
        raise validacion("fotos", "Máximo 5 fotos por reporte")
    es_residente = quien["rol"] == "Residente"
    captura = [c for c in ("medioOrigen", "fechaAviso", "residenteReportanteId", "nombreReferencia", "contactoReferencia")
               if c in d.model_fields_set]
    if es_residente and captura:
        raise prohibido("Un Residente no puede enviar campos de captura (RF-04)")
    descripcion = _descripcion(d.descripcion)
    _, subtipo, base = _resolver_categoria(db, d.categoriaId, d.subtipo)
    sugerida = "Urgente" if d.esPeligroso else base
    ubic, parte, ref = _resolver_ubicacion(db, d.ubicacion)
    es_unidad = d.ubicacion.tipo == "Unidad"
    if es_unidad and d.autorizaAcceso is None:
        raise validacion("autorizaAcceso", "Obligatorio si la ubicación es el interior de una unidad")
    if d.horariosAcceso is not None and d.autorizaAcceso is None:
        raise validacion("horariosAcceso", "Requiere autorizaAcceso")
    ahora = now_utc()
    if es_residente:
        medio, aviso = "Sistema", ahora
    else:
        if d.medioOrigen is None:
            raise validacion("medioOrigen", "Obligatorio al capturar en nombre de un tercero")
        if d.fechaAviso is None:
            raise validacion("fechaAviso", "Obligatoria al capturar en nombre de un tercero")
        medio, aviso = d.medioOrigen, to_utc(d.fechaAviso, "fechaAviso")
        if aviso > ahora:
            raise validacion("fechaAviso", "No puede ser una fecha futura")
    reportante = None
    if d.residenteReportanteId:
        if not db.execute("SELECT 1 FROM residente WHERE usuario_id=?", (d.residenteReportanteId,)).fetchone():
            raise validacion("residenteReportanteId", "No corresponde a un Residente")
        reportante = d.residenteReportanteId
    elif es_residente:
        reportante = quien["id"]
    elif not d.nombreReferencia or not d.nombreReferencia.strip():
        raise validacion("nombreReferencia", "Obligatorio si no se indica un residente reportante (RF-04)")

    # Archivos: cada uno se valida por separado; los inválidos se informan sin impedir el alta.
    aceptados, rechazados = [], []
    candidatos = [(f, "Foto") for f in fotos] + ([(video, "Video")] if video and video.filename else [])
    for f, tipo in candidatos:
        contenido = f.file.read()
        nombre = f.filename or "archivo"
        ok_tipo = (f.content_type in ("image/jpeg", "image/png")) if tipo == "Foto" else (f.content_type == "video/mp4")
        limite = config.MAX_FOTO_BYTES if tipo == "Foto" else config.MAX_VIDEO_BYTES
        if not ok_tipo:
            rechazados.append({"nombre": nombre, "motivo": "Solo se aceptan fotos JPEG o PNG" if tipo == "Foto" else "Solo se acepta video MP4"})
        elif len(contenido) > limite:
            rechazados.append({"nombre": nombre, "motivo": f"El archivo excede {limite // (1024 * 1024)} MB"})
        elif not contenido:
            rechazados.append({"nombre": nombre, "motivo": "El archivo está vacío"})
        else:
            aceptados.append((nombre, tipo, f.content_type, contenido))

    carpeta = None
    try:
        with tx(db, immediate=True):  # el folio se asigna dentro de la transacción: sin huecos ni repetidos
            n = db.execute("SELECT COALESCE(MAX(CAST(substr(folio, 4) AS INTEGER)), 0) FROM reporte").fetchone()[0] + 1
            folio = f"RY-{n:06d}"
            if es_unidad:  # RF-17: mismo piso de la misma torre y misma categoría, abierto
                dup = db.execute("""SELECT r.folio FROM reporte r JOIN unidad u1 ON u1.ubicacion_id = r.ubicacion_id
                                    JOIN unidad u2 ON u2.ubicacion_id = ?
                                    WHERE r.categoria_id=? AND r.estado NOT IN ('Cerrado','Cancelado','Unido')
                                      AND u1.torre = u2.torre AND u1.piso = u2.piso
                                    ORDER BY r.fecha_aviso DESC, r.folio DESC LIMIT 1""", (ubic, d.categoriaId)).fetchone()
            else:
                dup = db.execute("""SELECT folio FROM reporte WHERE categoria_id=? AND ubicacion_id=?
                                    AND estado NOT IN ('Cerrado','Cancelado','Unido')
                                    ORDER BY fecha_aviso DESC, folio DESC LIMIT 1""", (d.categoriaId, ubic)).fetchone()
            db.execute("""INSERT INTO reporte (folio, fecha_aviso, fecha_captura, medio_origen, descripcion, parte_afectada,
                          referencia, es_peligroso, autoriza_acceso, horarios_acceso, desde_cuando, habia_pasado_antes,
                          estado, prioridad_sugerida, ubicacion_id, reportante_id, capturado_por, categoria_id,
                          subtipo_nombre, nombre_referencia, contacto_referencia, posible_duplicado_de)
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'Reportado',?,?,?,?,?,?,?,?,?)""",
                       (folio, aviso, ahora, medio, descripcion, parte, ref, int(d.esPeligroso),
                        None if d.autorizaAcceso is None else int(d.autorizaAcceso), d.horariosAcceso, d.desdeCuando,
                        None if d.habiaPasadoAntes is None else int(d.habiaPasadoAntes), sugerida, ubic, reportante,
                        quien["id"], d.categoriaId, subtipo,
                        d.nombreReferencia.strip() if d.nombreReferencia else None, d.contactoReferencia,
                        dup["folio"] if dup else None))
            eid = _historial(db, folio, quien["id"], "CambioEstado")
            db.execute("INSERT INTO cambio_estado (entrada_id, estado_anterior, estado_nuevo) VALUES (?, NULL, 'Reportado')", (eid,))
            if aceptados:
                carpeta = config.UPLOAD_DIR / folio
                carpeta.mkdir(parents=True, exist_ok=True)
            for nombre, tipo, ctype, contenido in aceptados:
                aid = new_id()
                seguro = re.sub(r"[^A-Za-z0-9._-]", "_", nombre)[:80]
                destino = carpeta / f"{aid}_{seguro}"
                destino.write_bytes(contenido)
                if tipo == "Video" and db.execute("SELECT 1 FROM adjunto WHERE reporte_folio=? AND tipo='Video'", (folio,)).fetchone():
                    rechazados.append({"nombre": nombre, "motivo": "Solo se admite un video por reporte"})
                    destino.unlink()
                    continue
                db.execute("""INSERT INTO adjunto (id, reporte_folio, ciclo_numero, tipo, etapa, nombre, fecha, formato,
                              tamano_bytes, clave, subido_por) VALUES (?,?,NULL,?, 'Alta',?,?,?,?,?,?)""",
                           (aid, folio, tipo, nombre, now_utc(), ctype.split("/")[1], len(contenido),
                            f"{folio}/{destino.name}", quien["id"]))
    except BaseException:
        if carpeta:
            shutil.rmtree(carpeta, ignore_errors=True)
        raise
    detalle = report_detail(db, _reporte(db, folio))
    return responder({**detalle, "archivosRechazados": rechazados}, 201, f"/reports/{folio}", etag=True, etag_de_recurso=detalle)


# ------------------------------------------------------------------ duplicados posibles (consulta)
@router.get("/reports/possible-duplicates")
def find_possible_duplicates(categoriaId: str = Query(..., pattern=r"^[0-9a-fA-F-]{36}$"),
                             ubicacionTipo: Literal["Unidad", "AreaComun"] = Query(...),
                             ubicacionId: str = Query(..., pattern=r"^[0-9a-fA-F-]{36}$"), db=Depends(get_db)):
    if not db.execute("SELECT 1 FROM categoria WHERE id=?", (categoriaId,)).fetchone():
        raise validacion("categoriaId", "La categoría no existe")
    tabla = "unidad" if ubicacionTipo == "Unidad" else "area_comun"
    if not db.execute(f"SELECT 1 FROM {tabla} WHERE ubicacion_id=?", (ubicacionId,)).fetchone():
        raise validacion("ubicacionId", "La ubicación no existe")
    if ubicacionTipo == "Unidad":
        filas = db.execute("""SELECT r.* FROM reporte r JOIN unidad u1 ON u1.ubicacion_id=r.ubicacion_id
                              JOIN unidad u2 ON u2.ubicacion_id=? WHERE r.categoria_id=?
                              AND r.estado NOT IN ('Cerrado','Cancelado','Unido') AND u1.torre=u2.torre AND u1.piso=u2.piso
                              ORDER BY r.fecha_aviso DESC, r.folio DESC""", (ubicacionId, categoriaId)).fetchall()
    else:
        filas = db.execute("""SELECT * FROM reporte WHERE categoria_id=? AND ubicacion_id=?
                              AND estado NOT IN ('Cerrado','Cancelado','Unido') ORDER BY fecha_aviso DESC, folio DESC""",
                           (categoriaId, ubicacionId)).fetchall()
    return responder([report_summary(db, f) for f in filas])


# ------------------------------------------------------------------ detalle, corrección, borrado rechazado
@router.get("/reports/{folio}")
def get_report(folio: str = FolioP, db=Depends(get_db)):
    return responder(report_detail(db, _reporte(db, folio)), etag=True)


@router.patch("/reports/{folio}")
def correct_report(folio: str = FolioP, body: Any = Body(...), if_match: str = Header(...), db=Depends(get_db),
                   quien=Depends(actor)):
    r = _reporte(db, folio)
    verificar_if_match(if_match, report_detail(db, r))
    if r["estado"] in ("Cerrado", "Cancelado", "Unido"):
        raise conflicto("El reporte está en un estado final y ya no admite correcciones")
    d = S.parsear(S.ReportCorrection, body)
    campos = d.model_fields_set
    for c in ("categoriaId", "descripcion", "ubicacion"):
        if c in campos and getattr(d, c) is None:
            raise validacion(c, "No admite null")
    cat_id = d.categoriaId if "categoriaId" in campos else r["categoria_id"]
    if "subtipo" in campos:
        sub_in = d.subtipo
    else:
        sub_in = r["subtipo_nombre"] if cat_id == r["categoria_id"] else None
    cat, subtipo, base = _resolver_categoria(db, cat_id, sub_in)
    descripcion = _descripcion(d.descripcion) if "descripcion" in campos else r["descripcion"]
    if "ubicacion" in campos:
        ubic, parte, ref = _resolver_ubicacion(db, d.ubicacion)
    else:
        ubic, parte, ref = r["ubicacion_id"], r["parte_afectada"], r["referencia"]
    sugerida = r["prioridad_sugerida"]
    if cat_id != r["categoria_id"] or subtipo != r["subtipo_nombre"]:
        sugerida = "Urgente" if r["es_peligroso"] else base
    cambios = []  # (campo, anterior, nuevo): una VersionCorreccion por campo; la anterior se conserva (RNF-07)
    if cat_id != r["categoria_id"]:
        ant = db.execute("SELECT nombre FROM categoria WHERE id=?", (r["categoria_id"],)).fetchone()["nombre"]
        cambios.append(("categoria", ant, cat["nombre"]))
    if subtipo != r["subtipo_nombre"]:
        cambios.append(("subtipo", r["subtipo_nombre"], subtipo))
    if descripcion != r["descripcion"]:
        cambios.append(("descripcion", r["descripcion"], descripcion))
    if (ubic, parte, ref) != (r["ubicacion_id"], r["parte_afectada"], r["referencia"]):
        e = lambda i, p, rf: f"{db.execute('SELECT etiqueta FROM v_ubicacion WHERE id=?', (i,)).fetchone()['etiqueta']}" + \
            (f" ({p})" if p else "") + (f" [{rf}]" if rf else "")
        cambios.append(("ubicacion", e(r["ubicacion_id"], r["parte_afectada"], r["referencia"]), e(ubic, parte, ref)))
    if sugerida != r["prioridad_sugerida"]:
        cambios.append(("prioridadSugerida", r["prioridad_sugerida"], sugerida))
    if cambios:
        with tx(db):
            db.execute("""UPDATE reporte SET categoria_id=?, subtipo_nombre=?, descripcion=?, ubicacion_id=?,
                          parte_afectada=?, referencia=?, prioridad_sugerida=? WHERE folio=?""",
                       (cat_id, subtipo, descripcion, ubic, parte, ref, sugerida, folio))
            for campo, ant, nuevo in cambios:
                eid = _historial(db, folio, quien["id"], "Correccion", campo, ant, nuevo)
                db.execute("INSERT INTO version_correccion (entrada_id) VALUES (?)", (eid,))
    return responder(report_detail(db, _reporte(db, folio)), etag=True)


@router.delete("/reports/{folio}")
def delete_report_rejected(folio: str = FolioP, db=Depends(get_db)):
    _reporte(db, folio)
    raise prohibido("Los reportes no se eliminan (RNF-07)")


# ------------------------------------------------------------------ historial (RF-12)
@router.get("/reports/{folio}/history")
def get_report_history(folio: str = FolioP, db=Depends(get_db), pg=Depends(paginacion)):
    _reporte(db, folio)
    items = []
    filas = db.execute("""SELECT e.rowid AS orden, e.*, u.nombre AS autor, ce.estado_anterior, ce.estado_nuevo,
                          p.nombre AS proveedor, n.texto, c.monto, c.pagador
                          FROM entrada_historial e JOIN usuario u ON u.id = e.autor_id
                          LEFT JOIN cambio_estado ce ON ce.entrada_id = e.id
                          LEFT JOIN proveedor_sin_acceso p ON p.id = ce.actua_en_nombre_de_id
                          LEFT JOIN nota_avance n ON n.entrada_id = e.id LEFT JOIN costo c ON c.entrada_id = e.id
                          WHERE e.reporte_folio = ?""", (folio,)).fetchall()
    for f in filas:
        it = {"id": f["id"], "tipo": f["tipo"], "fecha": f["fecha"], "autor": f["autor"], "campo": f["campo"],
              "valorAnterior": f["valor_anterior"], "valorNuevo": f["valor_nuevo"], "comentario": f["comentario"],
              "actuaEnNombreDe": f["proveedor"]}
        if f["tipo"] == "CambioEstado":
            it.update(campo="estado", valorAnterior=f["estado_anterior"], valorNuevo=f["estado_nuevo"])
        elif f["tipo"] == "Nota":
            it["comentario"] = f["texto"]
        elif f["tipo"] == "Costo":
            it.update(campo="costo", valorNuevo=None if f["monto"] is None else str(f["monto"]),
                      comentario=" · ".join(x for x in (f"Pagador: {f['pagador']}", f["comentario"]) if x))
        items.append((f["fecha"], 0, f["orden"], it))
    for h in db.execute("SELECT d.*, u.nombre AS autor FROM detencion d JOIN usuario u ON u.id=d.autor_id WHERE d.reporte_folio=?", (folio,)):
        items.append((h["fecha_inicio"], 1, 0, {"id": h["id"], "tipo": "Detencion", "fecha": h["fecha_inicio"], "autor": h["autor"],
                                                 "campo": "motivo", "valorNuevo": h["motivo"], "comentario": h["texto_otro"]}))
        if h["fecha_fin"]:
            items.append((h["fecha_fin"], 1, 1, {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, h["id"] + "/fin")), "tipo": "Reanudacion",
                                                  "fecha": h["fecha_fin"], "autor": h["autor"], "campo": "motivo", "valorAnterior": h["motivo"]}))
    for c in db.execute("""SELECT c.*, u.nombre AS autor FROM confirmacion_residente c JOIN usuario u ON u.id=c.respondida_por
                           WHERE c.reporte_folio=?""", (folio,)):
        items.append((c["fecha"], 2, c["ciclo_numero"], {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{folio}/{c['ciclo_numero']}")),
                                                         "tipo": "Confirmacion", "fecha": c["fecha"], "autor": c["autor"],
                                                         "valorNuevo": c["respuesta"], "comentario": c["comentario"]}))
    items.sort(key=lambda x: x[:3])
    page, size = pg
    corte = items[(page - 1) * size: page * size]
    salida = []
    for _, _, _, it in corte:
        it["fecha"] = out_dt(it["fecha"])
        salida.append(it)
    return responder({"items": salida, "pagination": {"page": page, "pageSize": size, "total": len(items)}})


# ------------------------------------------------------------------ notas de avance
@router.get("/reports/{folio}/notes")
def list_notes(folio: str = FolioP, db=Depends(get_db)):
    _reporte(db, folio)
    return responder([note_out(n) for n in db.execute(NOTE_SQL, (folio,)).fetchall()])


@router.post("/reports/{folio}/notes")
def create_note(folio: str = FolioP, body: Any = Body(...), idempotency_key: Optional[str] = Header(default=None),
                db=Depends(get_db), quien=Depends(actor)):
    r = _reporte(db, folio)
    if r["estado"] not in ABIERTOS:
        raise conflicto("Las notas solo se agregan en Asignado o En proceso")
    d = S.parsear(S.NoteCreate, body)
    texto = S.no_vacio(d.texto, "texto")
    if len(texto) > 500:
        raise validacion("texto", "Máximo 500 caracteres")
    with tx(db):
        eid = _historial(db, folio, quien["id"], "Nota")
        db.execute("INSERT INTO nota_avance (entrada_id, texto) VALUES (?, ?)", (eid, texto))
    nota = next(n for n in db.execute(NOTE_SQL, (folio,)).fetchall() if n["id"] == eid)
    return responder(note_out(nota), 201, f"/reports/{folio}/notes/{eid}")


# ------------------------------------------------------------------ costos (RF-20)
@router.get("/reports/{folio}/costs")
def list_costs(folio: str = FolioP, db=Depends(get_db)):
    _reporte(db, folio)
    return responder([cost_out(c) for c in db.execute(COST_SQL, (folio,)).fetchall()])


@router.post("/reports/{folio}/costs")
def create_cost(folio: str = FolioP, body: Any = Body(...), idempotency_key: Optional[str] = Header(default=None),
                db=Depends(get_db), quien=Depends(actor)):
    _reporte(db, folio)
    d = S.parsear(S.CostCreate, body)
    if d.monto is not None and d.monto < 0:
        raise validacion("monto", "No puede ser negativo")
    if d.anulaCostoId:
        orig = db.execute("""SELECT 1 FROM costo c JOIN entrada_historial e ON e.id=c.entrada_id
                             WHERE c.entrada_id=? AND e.reporte_folio=?""", (d.anulaCostoId, folio)).fetchone()
        if not orig:
            raise validacion("anulaCostoId", "No es una entrada de costo de este reporte")
        if db.execute("SELECT 1 FROM costo WHERE anula_costo_id=?", (d.anulaCostoId,)).fetchone():
            raise validacion("anulaCostoId", "Ese costo ya fue anulado")
    with tx(db):
        eid = _historial(db, folio, quien["id"], "Costo", comentario=d.comentario)
        db.execute("INSERT INTO costo (entrada_id, monto, pagador, anula_costo_id) VALUES (?,?,?,?)",
                   (eid, d.monto, d.pagador, d.anulaCostoId))
    c = next(c for c in db.execute(COST_SQL, (folio,)).fetchall() if c["id"] == eid)
    return responder(cost_out(c), 201, f"/reports/{folio}/costs/{eid}")


# ------------------------------------------------------------------ detenciones (RF-18)
@router.post("/reports/{folio}/holds")
def create_hold(folio: str = FolioP, body: Any = Body(...), idempotency_key: Optional[str] = Header(default=None),
                db=Depends(get_db), quien=Depends(actor)):
    r = _reporte(db, folio)
    if r["estado"] not in ABIERTOS:
        raise conflicto("Solo se detiene un reporte Asignado o En proceso")
    if db.execute("SELECT 1 FROM detencion WHERE reporte_folio=? AND fecha_fin IS NULL", (folio,)).fetchone():
        raise conflicto("El reporte ya tiene una detención abierta")
    d = S.parsear(S.HoldCreate, body)
    if d.motivo == "Otro":
        S.no_vacio(d.textoOtro, "textoOtro")
    hid = new_id()
    with tx(db):
        db.execute("""INSERT INTO detencion (id, reporte_folio, motivo, texto_otro, fecha_inicio, autor_id)
                      VALUES (?,?,?,?,?,?)""", (hid, folio, d.motivo, d.textoOtro.strip() if d.textoOtro else None, now_utc(), quien["id"]))
    return responder(hold_out(db, db.execute("SELECT * FROM detencion WHERE id=?", (hid,)).fetchone()), 201, f"/reports/{folio}/holds/{hid}")


@router.patch("/reports/{folio}/holds/{holdId}")
def resume_hold(folio: str = FolioP, holdId: str = Path(..., pattern=r"^[0-9a-fA-F-]{36}$"), body: Any = Body(...),
                db=Depends(get_db)):
    _reporte(db, folio)
    h = db.execute("SELECT * FROM detencion WHERE id=? AND reporte_folio=?", (holdId, folio)).fetchone()
    if not h:
        raise no_encontrado("Detención no encontrada")
    S.parsear(S.HoldPatch, body)
    if h["fecha_fin"] is None:  # idempotente: reanudar una ya cerrada responde 200 sin cambios
        with tx(db):
            db.execute("UPDATE detencion SET fecha_fin=? WHERE id=?", (max(now_utc(), h["fecha_inicio"]), holdId))
    return responder(hold_out(db, db.execute("SELECT * FROM detencion WHERE id=?", (holdId,)).fetchone()))


# ------------------------------------------------------------------ visita programada (RF-15)
@router.put("/reports/{folio}/visit")
def schedule_visit(folio: str = FolioP, body: Any = Body(...), if_match: str = Header(...), db=Depends(get_db),
                   quien=Depends(actor)):
    r = _reporte(db, folio)
    verificar_if_match(if_match, report_detail(db, r))
    if r["estado"] not in ABIERTOS:
        raise conflicto("La visita se programa en Asignado o En proceso")
    d = S.parsear(S.VisitPut, body)
    fecha = to_utc(d.fechaVisita, "fechaVisita")
    if fecha < now_utc():
        raise validacion("fechaVisita", "La fecha no puede ser pasada")
    with tx(db):
        db.execute("UPDATE reporte SET fecha_visita=? WHERE folio=?", (fecha, folio))
        # El modelo no tiene un tipo de historial propio para la visita: se registra como corrección de campo.
        eid = _historial(db, folio, quien["id"], "Correccion", "fechaVisita", out_dt(r["fecha_visita"]), out_dt(fecha))
        db.execute("INSERT INTO version_correccion (entrada_id) VALUES (?)", (eid,))
    return responder(report_detail(db, _reporte(db, folio)), etag=True)


@router.delete("/reports/{folio}/visit")
def cancel_visit(folio: str = FolioP, db=Depends(get_db), quien=Depends(actor)):
    r = _reporte(db, folio)
    if r["estado"] not in ABIERTOS or r["fecha_visita"] is None:
        raise conflicto("No hay una visita programada que cancelar")
    with tx(db):
        db.execute("UPDATE reporte SET fecha_visita=NULL WHERE folio=?", (folio,))
        eid = _historial(db, folio, quien["id"], "Correccion", "fechaVisita", out_dt(r["fecha_visita"]), "Cancelada")
        db.execute("INSERT INTO version_correccion (entrada_id) VALUES (?)", (eid,))
    return Response(status_code=204)


# ------------------------------------------------------------------ indicaciones de persistencia (RF-19)
@router.get("/reports/{folio}/persistence-indications")
def list_persistence_indications(folio: str = FolioP, db=Depends(get_db)):
    _reporte(db, folio)
    filas = db.execute("""SELECT e.id, e.fecha, e.comentario, u.nombre AS residente FROM indicacion_persistencia ip
                          JOIN entrada_historial e ON e.id=ip.entrada_id JOIN usuario u ON u.id=ip.residente_id
                          WHERE e.reporte_folio=? ORDER BY e.fecha, e.rowid""", (folio,)).fetchall()
    return responder([{"id": f["id"], "fecha": out_dt(f["fecha"]), "residente": f["residente"], "comentario": f["comentario"]} for f in filas])


@router.post("/reports/{folio}/persistence-indications")
def create_persistence_indication(folio: str = FolioP, body: Any = Body(default={}),
                                  idempotency_key: Optional[str] = Header(default=None), db=Depends(get_db),
                                  quien=Depends(actor)):
    r = _reporte(db, folio)
    if not db.execute("SELECT 1 FROM residente WHERE usuario_id=?", (quien["id"],)).fetchone():
        raise prohibido("Solo un Residente indica que el problema persiste")
    if r["estado"] != "Cerrado":
        raise conflicto("Solo se indica la persistencia en un reporte Cerrado")
    plazo = db.execute("SELECT valor FROM parametro WHERE clave='plazoReaperturaDias'").fetchone()["valor"]
    cierre = db.execute("""SELECT e.fecha FROM entrada_historial e JOIN cambio_estado c ON c.entrada_id=e.id
                           WHERE e.reporte_folio=? AND c.estado_nuevo='Cerrado' ORDER BY e.fecha DESC, e.rowid DESC LIMIT 1""",
                        (folio,)).fetchone()
    limite = datetime.strptime(cierre["fecha"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) + timedelta(days=plazo) if cierre else None
    if limite is None or datetime.now(timezone.utc) > limite:
        raise conflicto(f"Pasaron más de {plazo:g} días desde el cierre: la Administración crea un reporte nuevo")
    d = S.parsear(S.PersistenceCreate, body)
    if d.comentario is not None and len(d.comentario) > 1000:
        raise peticion_invalida("El comentario excede 1000 caracteres")   # el YAML no declara 422 en esta operación
    with tx(db):
        eid = _historial(db, folio, quien["id"], "PersistenciaIndicada", comentario=d.comentario)
        db.execute("INSERT INTO indicacion_persistencia (entrada_id, residente_id) VALUES (?,?)", (eid, quien["id"]))
    f = db.execute("SELECT fecha, comentario FROM entrada_historial WHERE id=?", (eid,)).fetchone()
    return responder({"id": eid, "fecha": out_dt(f["fecha"]), "residente": quien["nombre"], "comentario": f["comentario"]},
                     201, f"/reports/{folio}/persistence-indications/{eid}")
