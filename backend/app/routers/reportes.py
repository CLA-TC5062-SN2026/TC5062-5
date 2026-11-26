"""Reportes y sus subrecursos CRUD (RF-03, RF-04, RF-10, RF-12, RF-15, RF-16, RF-17, RF-18, RF-19, RF-20, RF-26).

Las transiciones de estado están en `flujo.py`; los archivos, en `archivos.py`.
Toda lectura y toda acción pasan por la matriz de visibilidad (`visibilidad.py`, RNF-05): un reporte que el
usuario no puede ver responde 404, y los campos que la matriz le niega no se incluyen.
"""

import json
import re
import uuid
from datetime import date, timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, Body, Depends, File, Form, Header, Path, Query, Request, Response, UploadFile

from .. import config, reloj, schemas as S
from .. import notificaciones as N
from .. import visibilidad as V
from ..almacen import almacen
from ..db import get_db, tx
from ..reglas import historial as _historial, obtener_reporte as _reporte, parametro
from ..security import ADMIN, MANT, RES, UsuarioSesion, actor
from ..serial import COST_SQL, NOTE_SQL, cost_out, hold_out, note_out, report_detail, report_summary
from ..util import (
    FOLIO_RE,
    conflicto,
    day_end_utc,
    day_start_utc,
    new_id,
    no_encontrado,
    now_utc,
    out_dt,
    paginacion,
    peticion_invalida,
    prohibido,
    responder,
    to_utc,
    validacion,
    verificar_if_match,
)

router = APIRouter()
FolioP = Path(..., pattern=FOLIO_RE)
ABIERTOS = ("Asignado", "EnProceso")
ESTADOS_FINALES = ("Cerrado", "Cancelado", "Unido")
ORDEN_PRIORIDAD = (
    "CASE COALESCE(r.prioridad, r.prioridad_sugerida) WHEN 'Urgente' THEN 0 WHEN 'Normal' THEN 1 ELSE 2 END"
)


def detalle_para(db, quien: UsuarioSesion, folio: str) -> dict:
    """Detalle del reporte tal como lo puede ver `quien` (matriz 2.3)."""
    r = _reporte(db, folio)
    return V.recortar_detalle(db, quien, r, report_detail(db, r))


def visible(db, quien: UsuarioSesion, folio: str):
    """Reporte visible para `quien` o 404 (SRS 3.0)."""
    r = _reporte(db, folio)
    V.exigir_visible(db, quien, r)
    return r


def despachar(db) -> None:
    """Envía, fuera de la transacción, los correos que dejó pendientes el cambio (RF-11)."""
    N.procesar_correos(db)


# ------------------------------------------------------------------ validaciones compartidas
def _resolver_categoria(db, categoria_id, subtipo):
    cat = db.execute("SELECT * FROM categoria WHERE id=?", (categoria_id,)).fetchone()
    if not cat:
        raise validacion("categoriaId", "La categoría no existe")
    subs = db.execute("SELECT nombre, prioridad_sugerida FROM subtipo WHERE categoria_id=?", (categoria_id,)).fetchall()
    if subs and (subtipo is None or not subtipo.strip()):
        raise validacion("subtipo", "Indique el subtipo")  # RF-03-AC-10
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
        existe = db.execute(
            "SELECT b.activa FROM unidad x JOIN ubicacion b ON b.id=x.ubicacion_id WHERE x.ubicacion_id=?",
            (u.unidadId,),
        ).fetchone()
        uid, parte, ref = u.unidadId, u.parteAfectada, None
    else:
        if not u.areaComunId or u.unidadId:
            raise validacion(
                f"{campo}.areaComunId", "Una ubicación de tipo AreaComun requiere areaComunId (y no unidadId)"
            )
        if u.parteAfectada:
            raise validacion(f"{campo}.parteAfectada", "La parte afectada aplica solo a unidades (RD-13)")
        existe = db.execute(
            "SELECT b.activa FROM area_comun x JOIN ubicacion b ON b.id=x.ubicacion_id WHERE x.ubicacion_id=?",
            (u.areaComunId,),
        ).fetchone()
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
        raise validacion("descripcion", "La descripción debe tener entre 10 y 1,000 caracteres")  # RF-03-AC-2
    return texto.strip()


def _posibles_duplicados(db, ubicacion_tipo: str, ubicacion_id: str, categoria_id: str) -> list:
    """RF-17: reportes abiertos de la misma categoría en el mismo piso de la misma torre (unidades)
    o en la misma área común, del más reciente al más antiguo. Única definición de la regla."""
    marcadores = ",".join("?" * len(ESTADOS_FINALES))
    if ubicacion_tipo == "Unidad":
        sql = f"""SELECT r.* FROM reporte r JOIN unidad u1 ON u1.ubicacion_id = r.ubicacion_id
                  JOIN unidad u2 ON u2.ubicacion_id = ?
                  WHERE r.categoria_id = ? AND r.estado NOT IN ({marcadores})
                    AND u1.torre = u2.torre AND u1.piso = u2.piso
                  ORDER BY r.fecha_aviso DESC, r.folio DESC"""
        return db.execute(sql, (ubicacion_id, categoria_id, *ESTADOS_FINALES)).fetchall()
    sql = f"""SELECT * FROM reporte WHERE categoria_id = ? AND ubicacion_id = ? AND estado NOT IN ({marcadores})
              ORDER BY fecha_aviso DESC, folio DESC"""
    return db.execute(sql, (categoria_id, ubicacion_id, *ESTADOS_FINALES)).fetchall()


# ------------------------------------------------------------------ listado y búsqueda (RF-10, RF-12, RF-16)
FILTROS_DE_ADMINISTRACION = (
    "ubicacionTipo",
    "ubicacionId",
    "categoriaId",
    "estado",
    "prioridad",
    "responsableId",
    "medioOrigen",
    "avisoDesde",
    "avisoHasta",
    "texto",
)


# Filtro de RF-12 -> (condición SQL, cuántas veces se pasa el valor).
CONDICIONES_DE_BUSQUEDA = {
    "ubicacionTipo": ("(SELECT tipo FROM ubicacion WHERE id=r.ubicacion_id)=?", 1),
    "ubicacionId": ("(r.ubicacion_id=? OR r.ubicacion_origen_id=?)", 2),  # observada u origen (RF-12-AC-2)
    "categoriaId": ("r.categoria_id=?", 1),
    "estado": ("r.estado=?", 1),
    "prioridad": ("r.prioridad=?", 1),
    "responsableId": ("(r.responsable_usuario_id=? OR r.responsable_proveedor_id=?)", 2),
    "medioOrigen": ("r.medio_origen=?", 1),
    "avisoDesde": ("r.fecha_aviso >= ?", 1),
    "avisoHasta": ("r.fecha_aviso <= ?", 1),
    "texto": ("r.descripcion LIKE ? ESCAPE '\\'", 1),
}


@router.get("/reports")
def list_reports(
    request: Request,
    ubicacionTipo: Optional[Literal["Unidad", "AreaComun"]] = None,
    ubicacionId: Optional[str] = Query(None, pattern=r"^[0-9a-fA-F-]{36}$"),
    categoriaId: Optional[str] = Query(None, pattern=r"^[0-9a-fA-F-]{36}$"),
    estado: Optional[
        Literal["Reportado", "Asignado", "EnProceso", "Terminado", "Cerrado", "Cancelado", "Unido"]
    ] = None,
    prioridad: Optional[Literal["Urgente", "Normal", "Menor"]] = None,
    responsableId: Optional[str] = Query(None, pattern=r"^[0-9a-fA-F-]{36}$"),
    medioOrigen: Optional[S.MedioOrigen] = None,
    avisoDesde: Optional[date] = None,
    avisoHasta: Optional[date] = None,
    texto: Optional[str] = None,
    db=Depends(get_db),
    pg=Depends(paginacion),
    quien: UsuarioSesion = Depends(actor),
):
    """Una sola colección; el alcance y el orden los decide el rol del token (RNF-05)."""
    if quien.rol != ADMIN and any(f in request.query_params for f in FILTROS_DE_ADMINISTRACION):
        raise prohibido("La búsqueda es exclusiva de la Administración")  # RF-12-AC-5
    cond, p = V.condicion_sql(db, quien, solo_abiertos_mant=True)
    w = [cond]
    filtros = {
        "ubicacionTipo": ubicacionTipo, "ubicacionId": ubicacionId, "categoriaId": categoriaId, "estado": estado,
        "prioridad": prioridad, "responsableId": responsableId, "medioOrigen": medioOrigen,
        "avisoDesde": avisoDesde and day_start_utc(avisoDesde),
        "avisoHasta": avisoHasta and day_end_utc(avisoHasta),  # rangos inclusivos por días completos
        "texto": texto and "%" + texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%",
    }
    for nombre, valor in filtros.items():
        if valor:
            sql, veces = CONDICIONES_DE_BUSQUEDA[nombre]
            w.append(sql)
            p += [valor] * veces
    page, size = pg
    sql_from = "FROM reporte r WHERE " + " AND ".join(w)
    # RF-16: Mantenimiento por prioridad y, a igual prioridad, del aviso más antiguo al más reciente.
    orden = (
        f"{ORDEN_PRIORIDAD}, r.fecha_aviso ASC, r.folio ASC"
        if quien.rol == MANT
        else "r.fecha_aviso DESC, r.folio DESC"
    )
    total = db.execute(f"SELECT count(*) {sql_from}", p).fetchone()[0]
    filas = db.execute(
        f"SELECT r.* {sql_from} ORDER BY {orden} LIMIT ? OFFSET ?", p + [size, (page - 1) * size]
    ).fetchall()
    return responder(
        {
            "items": [V.recortar_resumen(quien, f, report_summary(db, f)) for f in filas],
            "pagination": {"page": page, "pageSize": size, "total": total},
        }
    )


# ------------------------------------------------------------------ alta (RF-03 / RF-04)
CAMPOS_DE_CAPTURA = ("medioOrigen", "fechaAviso", "residenteReportanteId", "nombreReferencia", "contactoReferencia")
TIPOS_FOTO = ("image/jpeg", "image/png")
TIPO_VIDEO = "video/mp4"
MAX_FOTOS_POR_ETAPA = 5


def _leer_datos(datos: str) -> S.ReportCreate:
    """Parte `datos` del formulario multipart -> ReportCreate validado."""
    try:
        return S.parsear(S.ReportCreate, json.loads(datos))
    except json.JSONDecodeError as exc:
        raise peticion_invalida("La parte `datos` no es un JSON válido") from exc


def _validar_campos_de_captura(d: S.ReportCreate, es_residente: bool) -> None:
    """RF-04: los campos de captura en nombre de un tercero no los puede enviar un Residente."""
    if es_residente and any(c in d.model_fields_set for c in CAMPOS_DE_CAPTURA):
        raise prohibido("Un Residente no puede enviar campos de captura (RF-04)")


def _validar_ubicacion_del_residente(db, d: S.ReportCreate, quien: UsuarioSesion) -> None:
    """RF-03-AC-4: el Residente solo reporta en su unidad o en un área común."""
    if d.ubicacion.tipo != "Unidad":
        return
    v = V.vinculacion_vigente(db, quien.id)
    if not v or v["unidad_id"] != d.ubicacion.unidadId:
        raise validacion("ubicacion", "Solo puede reportar en su unidad o en áreas comunes")


def _validar_acceso(d: S.ReportCreate, es_residente: bool) -> None:
    """Autorización y horarios de acceso al interior de una unidad (RF-03-AC-3, RF-04-AC-4)."""
    if d.ubicacion.tipo == "Unidad" and d.autorizaAcceso is None:
        raise validacion(
            "autorizaAcceso",
            "Indique si autoriza el acceso a su departamento"
            if es_residente
            else "Indique si el ocupante autoriza el acceso",
        )
    if d.horariosAcceso is not None and d.autorizaAcceso is None:
        raise validacion("horariosAcceso", "Requiere autorizaAcceso")


def _validar_peligro(d: S.ReportCreate) -> None:
    if d.esPeligroso is None:  # RF-03-AC-6, RF-04-AC-9
        raise validacion("esPeligroso", "Indique si el problema es peligroso o está empeorando")


def _origen_del_aviso(d: S.ReportCreate, es_residente: bool, ahora: str) -> tuple[str, str]:
    """(medio de origen, fecha de aviso): el Residente reporta por el Sistema en este momento;
    quien captura por un tercero indica medio y fecha, que no puede ser futura (RF-04)."""
    if es_residente:
        return "Sistema", ahora
    if d.medioOrigen is None:
        raise validacion("medioOrigen", "Indique el medio por el que llegó el aviso")
    if d.fechaAviso is None:
        raise validacion("fechaAviso", "Indique la fecha y hora del aviso")
    aviso = to_utc(d.fechaAviso, "fechaAviso")
    if aviso > ahora:
        raise validacion("fechaAviso", "La fecha del aviso no puede ser futura")  # RF-04-AC-2
    return d.medioOrigen, aviso


def _reportante(db, d: S.ReportCreate, quien: UsuarioSesion, es_residente: bool) -> Optional[str]:
    """Residente que reporta: el indicado, el propio Residente o ninguno (entonces se exige nombreReferencia)."""
    if d.residenteReportanteId:
        if not db.execute("SELECT 1 FROM residente WHERE usuario_id=?", (d.residenteReportanteId,)).fetchone():
            raise validacion("residenteReportanteId", "No corresponde a un Residente")
        return d.residenteReportanteId
    if es_residente:
        return quien.id
    if not d.nombreReferencia or not d.nombreReferencia.strip():
        raise validacion("nombreReferencia", "Indique el nombre de quien reporta")  # RF-04-AC-6
    return None


def validar_archivos(fotos: list[UploadFile], video: Optional[UploadFile] = None) -> tuple[list, list]:
    """RF-05: cada archivo se valida por separado; los inválidos se informan sin impedir la operación.
    Devuelve (aceptados, rechazados); aceptados = [(nombre, tipo, content_type, contenido)]."""
    aceptados, rechazados = [], []
    candidatos = [(f, "Foto") for f in fotos if f.filename] + ([(video, "Video")] if video and video.filename else [])
    for archivo, tipo in candidatos:
        contenido = archivo.file.read()
        nombre = archivo.filename or "archivo"
        es_foto = tipo == "Foto"
        tipo_valido = archivo.content_type in TIPOS_FOTO if es_foto else archivo.content_type == TIPO_VIDEO
        limite = config.MAX_FOTO_BYTES if es_foto else config.MAX_VIDEO_BYTES
        if not tipo_valido:
            motivo = "Formato no permitido: use JPEG o PNG" if es_foto else "Formato no permitido: use MP4"
            rechazados.append({"nombre": nombre, "motivo": motivo})  # RF-05-AC-2
        elif len(contenido) > limite:
            mb = limite // (1024 * 1024)
            rechazados.append(
                {"nombre": nombre, "motivo": f"La foto supera {mb} MB" if es_foto else f"El video supera {mb} MB"}
            )  # RF-05-AC-3, AC-6
        elif not contenido:
            rechazados.append({"nombre": nombre, "motivo": "El archivo está vacío"})
        else:
            aceptados.append((nombre, tipo, archivo.content_type, contenido))
    return aceptados, rechazados


def _siguiente_folio(db) -> str:
    """Debe llamarse dentro de una transacción IMMEDIATE: así no hay huecos ni folios repetidos."""
    n = db.execute("SELECT COALESCE(MAX(CAST(substr(folio, 4) AS INTEGER)), 0) FROM reporte").fetchone()[0] + 1
    return f"RY-{n:06d}"


def _insertar_reporte(db, folio: str, valores: dict) -> None:
    """INSERT del reporte en estado Reportado y su primera entrada de historial (CambioEstado)."""
    db.execute(
        """INSERT INTO reporte (folio, fecha_aviso, fecha_captura, medio_origen, descripcion, parte_afectada,
                  referencia, es_peligroso, autoriza_acceso, horarios_acceso, desde_cuando, habia_pasado_antes,
                  estado, prioridad_sugerida, ubicacion_id, reportante_id, capturado_por, categoria_id,
                  subtipo_nombre, nombre_referencia, contacto_referencia, posible_duplicado_de)
                  VALUES (:folio, :fecha_aviso, :fecha_captura, :medio_origen, :descripcion, :parte_afectada,
                  :referencia, :es_peligroso, :autoriza_acceso, :horarios_acceso, :desde_cuando, :habia_pasado_antes,
                  'Reportado', :prioridad_sugerida, :ubicacion_id, :reportante_id, :capturado_por, :categoria_id,
                  :subtipo_nombre, :nombre_referencia, :contacto_referencia, :posible_duplicado_de)""",
        {**valores, "folio": folio},
    )
    eid = _historial(db, folio, valores["capturado_por"], "CambioEstado")
    db.execute(
        "INSERT INTO cambio_estado (entrada_id, estado_anterior, estado_nuevo) VALUES (?, NULL, 'Reportado')", (eid,)
    )


def guardar_adjuntos(
    db,
    folio: str,
    aceptados: list,
    rechazados: list,
    autor_id: str,
    escritos: list,
    etapa: str = "Alta",
    ciclo: Optional[int] = None,
) -> None:
    """Guarda los archivos aceptados en el almacén (RNF-08) y registra cada adjunto. Agrega a `escritos` las
    claves guardadas para que quien llama las deshaga si la transacción falla."""
    for nombre, tipo, content_type, contenido in aceptados:
        if (
            tipo == "Video"
            and db.execute("SELECT 1 FROM adjunto WHERE reporte_folio=? AND tipo='Video'", (folio,)).fetchone()
        ):
            rechazados.append({"nombre": nombre, "motivo": "Solo se admite un video por reporte"})
            continue
        aid = new_id()
        clave = f"{folio}/{aid}_{re.sub(r'[^A-Za-z0-9._-]', '_', nombre)[:80]}"
        almacen().guardar(clave, contenido, content_type)
        escritos.append(clave)
        db.execute(
            """INSERT INTO adjunto (id, reporte_folio, ciclo_numero, tipo, etapa, nombre, fecha, formato,
                      tamano_bytes, clave, subido_por) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                aid,
                folio,
                ciclo,
                tipo,
                etapa,
                nombre,
                now_utc(),
                content_type.split("/")[1],
                len(contenido),
                clave,
                autor_id,
            ),
        )


def deshacer_archivos(escritos: list) -> None:
    """Compensación: borra del almacén los archivos de una operación que no se guardó."""
    for clave in escritos:
        try:
            almacen().borrar(clave)
        except Exception:  # noqa: BLE001 — la limpieza nunca oculta el error original
            pass


def _registrar_reporte(db, valores: dict, ubicacion_tipo: str, aceptados: list, rechazados: list) -> str:
    """Folio, detección de duplicados (RF-17), INSERT, historial, adjuntos y avisos (RF-11) en una sola
    transacción. Si algo falla se revierte la base y se borran los archivos ya escritos."""
    escritos: list = []
    try:
        with tx(db, immediate=True):
            folio = _siguiente_folio(db)
            duplicados = _posibles_duplicados(db, ubicacion_tipo, valores["ubicacion_id"], valores["categoria_id"])
            valores["posible_duplicado_de"] = duplicados[0]["folio"] if duplicados else None
            _insertar_reporte(db, folio, valores)
            guardar_adjuntos(db, folio, aceptados, rechazados, valores["capturado_por"], escritos)
            N.al_alta(db, _reporte(db, folio))
    except BaseException:
        deshacer_archivos(escritos)
        raise
    return folio


def _como_entero(valor: Optional[bool]) -> Optional[int]:
    return None if valor is None else int(valor)


@router.post("/reports")
def create_report(
    datos: str = Form(...),
    fotos: list[UploadFile] = File(default=[]),
    video: Optional[UploadFile] = File(default=None),
    idempotency_key: Optional[str] = Header(default=None),  # aceptado; ver revision_sql.md
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    """Coordina el alta: valida en el orden del contrato y registra en una transacción."""
    d = _leer_datos(datos)
    if len([f for f in fotos if f.filename]) > MAX_FOTOS_POR_ETAPA:
        raise validacion("fotos", "Máximo 5 fotografías por etapa")  # RF-05-AC-4
    es_residente = quien.rol == RES
    _validar_campos_de_captura(d, es_residente)
    descripcion = _descripcion(d.descripcion)
    _, subtipo, prioridad_base = _resolver_categoria(db, d.categoriaId, d.subtipo)
    ubicacion_id, parte, referencia = _resolver_ubicacion(db, d.ubicacion)
    if es_residente:
        _validar_ubicacion_del_residente(db, d, quien)
    _validar_peligro(d)
    _validar_acceso(d, es_residente)
    ahora = now_utc()
    medio, aviso = _origen_del_aviso(d, es_residente, ahora)
    reportante = _reportante(db, d, quien, es_residente)
    aceptados, rechazados = validar_archivos(fotos, video)

    valores = {
        "fecha_aviso": aviso,
        "fecha_captura": ahora,
        "medio_origen": medio,
        "descripcion": descripcion,
        "parte_afectada": parte,
        "referencia": referencia,
        "es_peligroso": int(d.esPeligroso),
        "autoriza_acceso": _como_entero(d.autorizaAcceso),
        "horarios_acceso": d.horariosAcceso,
        "desde_cuando": d.desdeCuando,
        "habia_pasado_antes": _como_entero(d.habiaPasadoAntes),
        "prioridad_sugerida": "Urgente" if d.esPeligroso else prioridad_base,
        "ubicacion_id": ubicacion_id,
        "reportante_id": reportante,
        "capturado_por": quien.id,
        "categoria_id": d.categoriaId,
        "subtipo_nombre": subtipo,
        "nombre_referencia": d.nombreReferencia.strip() if d.nombreReferencia else None,
        "contacto_referencia": d.contactoReferencia,
    }
    folio = _registrar_reporte(db, valores, d.ubicacion.tipo, aceptados, rechazados)
    despachar(db)
    detalle = detalle_para(db, quien, folio)
    return responder(
        {**detalle, "archivosRechazados": rechazados}, 201, f"/reports/{folio}", etag=True, etag_de_recurso=detalle
    )


# ------------------------------------------------------------------ duplicados posibles (consulta)
@router.get("/reports/possible-duplicates")
def find_possible_duplicates(
    categoriaId: str = Query(..., pattern=r"^[0-9a-fA-F-]{36}$"),
    ubicacionTipo: Literal["Unidad", "AreaComun"] = Query(...),
    ubicacionId: str = Query(..., pattern=r"^[0-9a-fA-F-]{36}$"),
    db=Depends(get_db),
):
    if not db.execute("SELECT 1 FROM categoria WHERE id=?", (categoriaId,)).fetchone():
        raise validacion("categoriaId", "La categoría no existe")
    tabla = "unidad" if ubicacionTipo == "Unidad" else "area_comun"
    if not db.execute(f"SELECT 1 FROM {tabla} WHERE ubicacion_id=?", (ubicacionId,)).fetchone():
        raise validacion("ubicacionId", "La ubicación no existe")
    filas = _posibles_duplicados(db, ubicacionTipo, ubicacionId, categoriaId)
    return responder([report_summary(db, f) for f in filas])


# ------------------------------------------------------------------ detalle, corrección, borrado rechazado
@router.get("/reports/{folio}")
def get_report(folio: str = FolioP, db=Depends(get_db), quien: UsuarioSesion = Depends(actor)):
    visible(db, quien, folio)
    return responder(detalle_para(db, quien, folio), etag=True)


def _exigir_corregible(quien: UsuarioSesion, r) -> None:
    """RF-26: el residente corrige solo lo que registró, y solo en Reportado (desde Asignado: 409, RF-26-AC-3)."""
    if quien.rol != RES:
        return
    if r["reportante_id"] != quien.id or r["capturado_por"] != quien.id:
        raise prohibido("Solo el residente que registró el reporte puede corregirlo")
    if r["estado"] != "Reportado":
        raise conflicto("Transición no permitida")


def _ubicacion_corregida(db, quien: UsuarioSesion, r, d, campos) -> tuple:
    if "ubicacion" not in campos:
        return r["ubicacion_id"], r["parte_afectada"], r["referencia"]
    if quien.rol == RES and d.ubicacion.tipo == "Unidad":
        v = V.vinculacion_vigente(db, quien.id)
        if not v or v["unidad_id"] != d.ubicacion.unidadId:
            raise validacion("ubicacion", "Solo puede reportar en su unidad o en áreas comunes")
    return _resolver_ubicacion(db, d.ubicacion)


def _valores_corregidos(db, quien: UsuarioSesion, r, d) -> dict:
    """Valores finales del reporte: los enviados en el merge-patch y, para el resto, los actuales."""
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
    sugerida = r["prioridad_sugerida"]
    if cat_id != r["categoria_id"] or subtipo != r["subtipo_nombre"]:
        sugerida = "Urgente" if r["es_peligroso"] else base  # RF-26-AC-5
    return {
        "categoria_id": cat_id,
        "categoria": cat["nombre"],
        "subtipo_nombre": subtipo,
        "descripcion": _descripcion(d.descripcion) if "descripcion" in campos else r["descripcion"],
        "ubicacion": _ubicacion_corregida(db, quien, r, d, campos),
        "prioridad_sugerida": sugerida,
    }


def _cambios_de_correccion(db, r, n: dict) -> list:
    """(campo, anterior, nuevo): una VersionCorreccion por campo; la anterior se conserva (RNF-07)."""

    def etiqueta(i, p, rf):
        base_ = db.execute("SELECT etiqueta FROM v_ubicacion WHERE id=?", (i,)).fetchone()["etiqueta"]
        return base_ + (f" ({p})" if p else "") + (f" [{rf}]" if rf else "")

    cambios = []
    if n["categoria_id"] != r["categoria_id"]:
        ant = db.execute("SELECT nombre FROM categoria WHERE id=?", (r["categoria_id"],)).fetchone()["nombre"]
        cambios.append(("categoria", ant, n["categoria"]))
    for campo, columna in (("subtipo", "subtipo_nombre"), ("descripcion", "descripcion")):
        if n[columna] != r[columna]:
            cambios.append((campo, r[columna], n[columna]))
    anterior = (r["ubicacion_id"], r["parte_afectada"], r["referencia"])
    if n["ubicacion"] != anterior:
        cambios.append(("ubicacion", etiqueta(*anterior), etiqueta(*n["ubicacion"])))
    if n["prioridad_sugerida"] != r["prioridad_sugerida"]:
        cambios.append(("prioridadSugerida", r["prioridad_sugerida"], n["prioridad_sugerida"]))
    return cambios


@router.patch("/reports/{folio}")
def correct_report(
    folio: str = FolioP,
    body: Any = Body(...),
    if_match: str = Header(...),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    _exigir_corregible(quien, r)
    verificar_if_match(if_match, detalle_para(db, quien, folio))
    if r["estado"] in ESTADOS_FINALES:
        raise conflicto("El reporte está en un estado final y ya no admite correcciones")
    n = _valores_corregidos(db, quien, r, S.parsear(S.ReportCorrection, body))
    cambios = _cambios_de_correccion(db, r, n)
    if cambios:
        ubic, parte, ref = n["ubicacion"]
        with tx(db):
            db.execute(
                """UPDATE reporte SET categoria_id=?, subtipo_nombre=?, descripcion=?, ubicacion_id=?,
                          parte_afectada=?, referencia=?, prioridad_sugerida=? WHERE folio=?""",
                (n["categoria_id"], n["subtipo_nombre"], n["descripcion"], ubic, parte, ref,
                 n["prioridad_sugerida"], folio),
            )
            for campo, ant, nuevo in cambios:
                eid = _historial(db, folio, quien.id, "Correccion", campo, ant, nuevo)
                db.execute("INSERT INTO version_correccion (entrada_id) VALUES (?)", (eid,))
    return responder(detalle_para(db, quien, folio), etag=True)


@router.delete("/reports/{folio}")
def delete_report_rejected(folio: str = FolioP, db=Depends(get_db)):
    _reporte(db, folio)
    raise prohibido("Los reportes no se eliminan (RNF-07)")


# ------------------------------------------------------------------ historial (RF-12)
def _item_de_historial(f) -> dict:
    """Una entrada de historial -> HistoryItem (estado, nota y costo se presentan como cambio de un campo)."""
    it = {
        "id": f["id"],
        "tipo": f["tipo"],
        "fecha": f["fecha"],
        "autor": f["autor"],
        "campo": f["campo"],
        "valorAnterior": f["valor_anterior"],
        "valorNuevo": f["valor_nuevo"],
        "comentario": f["comentario"],
        "actuaEnNombreDe": f["proveedor"],
    }
    if f["tipo"] == "CambioEstado":
        it.update(campo="estado", valorAnterior=f["estado_anterior"], valorNuevo=f["estado_nuevo"])
        if f["proveedor"]:  # RF-07-AC-10: el usuario interno y el proveedor en cuyo nombre registró
            it["autor"] = f"{f['autor']} (en nombre de {f['proveedor']})"
    elif f["tipo"] == "Nota":
        it["comentario"] = f["texto"]
    elif f["tipo"] == "Costo":
        it.update(
            campo="costo",
            valorNuevo=None if f["monto"] is None else str(f["monto"]),
            comentario=" · ".join(x for x in (f"Pagador: {f['pagador']}", f["comentario"]) if x),
        )
    return it


@router.get("/reports/{folio}/history")
def get_report_history(
    folio: str = FolioP, db=Depends(get_db), pg=Depends(paginacion), quien: UsuarioSesion = Depends(actor)
):
    visible(db, quien, folio)
    items = []
    filas = db.execute(
        """SELECT e.rowid AS orden, e.*, u.nombre AS autor, ce.estado_anterior, ce.estado_nuevo,
                          p.nombre AS proveedor, n.texto, c.monto, c.pagador
                          FROM entrada_historial e JOIN usuario u ON u.id = e.autor_id
                          LEFT JOIN cambio_estado ce ON ce.entrada_id = e.id
                          LEFT JOIN proveedor_sin_acceso p ON p.id = ce.actua_en_nombre_de_id
                          LEFT JOIN nota_avance n ON n.entrada_id = e.id LEFT JOIN costo c ON c.entrada_id = e.id
                          WHERE e.reporte_folio = ?""",
        (folio,),
    ).fetchall()
    for f in filas:
        it = _item_de_historial(f)
        items.append((f["fecha"], 0, f["orden"], it))
    for h in db.execute(
        "SELECT d.*, u.nombre AS autor FROM detencion d JOIN usuario u ON u.id=d.autor_id WHERE d.reporte_folio=?",
        (folio,),
    ):
        items.append(
            (
                h["fecha_inicio"],
                1,
                0,
                {
                    "id": h["id"],
                    "tipo": "Detencion",
                    "fecha": h["fecha_inicio"],
                    "autor": h["autor"],
                    "campo": "motivo",
                    "valorNuevo": h["motivo"],
                    "comentario": h["texto_otro"],
                },
            )
        )
        if h["fecha_fin"]:
            items.append(
                (
                    h["fecha_fin"],
                    1,
                    1,
                    {
                        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, h["id"] + "/fin")),
                        "tipo": "Reanudacion",
                        "fecha": h["fecha_fin"],
                        "autor": h["autor"],
                        "campo": "motivo",
                        "valorAnterior": h["motivo"],
                    },
                )
            )
    for c in db.execute(
        """SELECT c.*, u.nombre AS autor FROM confirmacion_residente c JOIN usuario u ON u.id=c.respondida_por
                           WHERE c.reporte_folio=?""",
        (folio,),
    ):
        items.append(
            (
                c["fecha"],
                2,
                c["ciclo_numero"],
                {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{folio}/{c['ciclo_numero']}")),
                    "tipo": "Confirmacion",
                    "fecha": c["fecha"],
                    "autor": c["autor"],
                    "valorNuevo": c["respuesta"],
                    "comentario": c["comentario"],
                },
            )
        )
    # RF-11: cada envío deja constancia (canal, fecha y hora) en el historial del reporte.
    for a in db.execute(
        """SELECT a.id, a.tipo, a.evento, a.fecha, e.estado, e.destinatario, u.nombre AS usuario
                           FROM aviso a LEFT JOIN envio_correo e ON e.aviso_id = a.id
                           LEFT JOIN aviso_sistema s ON s.aviso_id = a.id LEFT JOIN usuario u ON u.id =
                               s.destinatario_usuario_id
                           WHERE a.reporte_folio = ?""",
        (folio,),
    ):
        destino = a["usuario"] if a["tipo"] == "Sistema" else a["destinatario"]
        items.append(
            (
                a["fecha"],
                3,
                0,
                {
                    "id": a["id"],
                    "tipo": "AvisoEnviado",
                    "fecha": a["fecha"],
                    "autor": "Sistema",
                    "canal": a["tipo"],
                    "campo": "evento",
                    "valorNuevo": a["evento"],
                    "comentario": f"Para {destino}" + (f" · {a['estado']}" if a["estado"] else ""),
                },
            )
        )
    items = [x for x in items if V.tipo_historial_visible(quien, x[3]["tipo"])]
    items.sort(key=lambda x: x[:3])
    page, size = pg
    corte = items[(page - 1) * size : page * size]
    salida = []
    for _, _, _, it in corte:
        it["fecha"] = out_dt(it["fecha"])
        salida.append(it)
    return responder({"items": salida, "pagination": {"page": page, "pageSize": size, "total": len(items)}})


# ------------------------------------------------------------------ notas de avance (RF-15)
@router.get("/reports/{folio}/notes")
def list_notes(folio: str = FolioP, db=Depends(get_db), quien: UsuarioSesion = Depends(actor)):
    visible(db, quien, folio)
    return responder([note_out(n) for n in db.execute(NOTE_SQL, (folio,)).fetchall()])


@router.post("/reports/{folio}/notes")
def create_note(
    folio: str = FolioP,
    body: Any = Body(...),
    idempotency_key: Optional[str] = Header(default=None),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    if r["estado"] not in ABIERTOS:
        raise conflicto("Las notas solo se agregan en Asignado o En proceso")
    d = S.parsear(S.NoteCreate, body)
    texto = S.no_vacio(d.texto, "texto")
    if len(texto) > 500:
        raise validacion("texto", "La nota debe tener entre 1 y 500 caracteres")
    with tx(db):
        eid = _historial(db, folio, quien.id, "Nota")
        db.execute("INSERT INTO nota_avance (entrada_id, texto) VALUES (?, ?)", (eid, texto))
    nota = next(n for n in db.execute(NOTE_SQL, (folio,)).fetchall() if n["id"] == eid)
    return responder(note_out(nota), 201, f"/reports/{folio}/notes/{eid}")


# ------------------------------------------------------------------ costos (RF-20)
@router.get("/reports/{folio}/costs")
def list_costs(folio: str = FolioP, db=Depends(get_db)):
    _reporte(db, folio)
    return responder([cost_out(c) for c in db.execute(COST_SQL, (folio,)).fetchall()])


@router.post("/reports/{folio}/costs")
def create_cost(
    folio: str = FolioP,
    body: Any = Body(...),
    idempotency_key: Optional[str] = Header(default=None),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    _reporte(db, folio)
    d = S.parsear(S.CostCreate, body)
    if d.monto is not None and d.monto < 0:
        raise validacion("monto", "El monto no puede ser negativo")  # RF-20-AC-3
    if d.anulaCostoId:
        orig = db.execute(
            """SELECT 1 FROM costo c JOIN entrada_historial e ON e.id=c.entrada_id
                             WHERE c.entrada_id=? AND e.reporte_folio=?""",
            (d.anulaCostoId, folio),
        ).fetchone()
        if not orig:
            raise validacion("anulaCostoId", "No es una entrada de costo de este reporte")
        if db.execute("SELECT 1 FROM costo WHERE anula_costo_id=?", (d.anulaCostoId,)).fetchone():
            raise validacion("anulaCostoId", "Ese costo ya fue anulado")
    with tx(db):
        eid = _historial(db, folio, quien.id, "Costo", comentario=d.comentario)
        db.execute(
            "INSERT INTO costo (entrada_id, monto, pagador, anula_costo_id) VALUES (?,?,?,?)",
            (eid, d.monto, d.pagador, d.anulaCostoId),
        )
    c = next(c for c in db.execute(COST_SQL, (folio,)).fetchall() if c["id"] == eid)
    return responder(cost_out(c), 201, f"/reports/{folio}/costs/{eid}")


# ------------------------------------------------------------------ detenciones (RF-18)
MOTIVO_LEGIBLE = {
    "AccesoAlDepartamento": "Acceso al departamento",
    "EsperaDeProveedor": "Espera de proveedor",
    "EsperaDePieza": "Espera de pieza",
    "EsperaDeAutorizacionDeGasto": "Espera de autorización de gasto",
    "Otro": "Otro",
}


@router.post("/reports/{folio}/holds")
def create_hold(
    folio: str = FolioP,
    body: Any = Body(...),
    idempotency_key: Optional[str] = Header(default=None),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    if r["estado"] not in ABIERTOS:
        raise conflicto("Transición no permitida")  # RF-18-AC-4
    if db.execute("SELECT 1 FROM detencion WHERE reporte_folio=? AND fecha_fin IS NULL", (folio,)).fetchone():
        raise conflicto("El reporte ya está detenido")
    d = S.parsear(S.HoldCreate, body)
    if d.motivo == "Otro":
        S.no_vacio(d.textoOtro, "textoOtro")
    hid = new_id()
    with tx(db):
        db.execute(
            """INSERT INTO detencion (id, reporte_folio, motivo, texto_otro, fecha_inicio, autor_id)
                      VALUES (?,?,?,?,?,?)""",
            (hid, folio, d.motivo, d.textoOtro.strip() if d.textoOtro else None, now_utc(), quien.id),
        )
        motivo = d.textoOtro.strip() if d.motivo == "Otro" else MOTIVO_LEGIBLE[d.motivo]
        N.al_residente(db, r, "Detenido", f"La atención de {folio} quedó detenida. Motivo: «{motivo}».")  # RF-18-AC-5
    despachar(db)
    return responder(
        hold_out(db, db.execute("SELECT * FROM detencion WHERE id=?", (hid,)).fetchone()),
        201,
        f"/reports/{folio}/holds/{hid}",
    )


@router.patch("/reports/{folio}/holds/{holdId}")
def resume_hold(
    folio: str = FolioP,
    holdId: str = Path(..., pattern=r"^[0-9a-fA-F-]{36}$"),
    body: Any = Body(...),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    h = db.execute("SELECT * FROM detencion WHERE id=? AND reporte_folio=?", (holdId, folio)).fetchone()
    if not h:
        raise no_encontrado("Detención no encontrada")
    S.parsear(S.HoldPatch, body)
    if h["fecha_fin"] is None:  # idempotente: reanudar una ya cerrada responde 200 sin cambios
        with tx(db):
            db.execute("UPDATE detencion SET fecha_fin=? WHERE id=?", (max(now_utc(), h["fecha_inicio"]), holdId))
            N.al_residente(db, r, "Reanudado", f"Se reanudó la atención de {folio}.")
        despachar(db)
    return responder(hold_out(db, db.execute("SELECT * FROM detencion WHERE id=?", (holdId,)).fetchone()))


# ------------------------------------------------------------------ visita programada (RF-15)
@router.put("/reports/{folio}/visit")
def schedule_visit(
    folio: str = FolioP,
    body: Any = Body(...),
    if_match: str = Header(...),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    verificar_if_match(if_match, detalle_para(db, quien, folio))
    if r["estado"] not in ABIERTOS:
        raise conflicto("La visita se programa en Asignado o En proceso")
    d = S.parsear(S.VisitPut, body)
    fecha = to_utc(d.fechaVisita, "fechaVisita")
    if fecha < now_utc():
        raise validacion("fechaVisita", "La fecha de la visita no puede ser pasada")
    with tx(db):
        db.execute("UPDATE reporte SET fecha_visita=? WHERE folio=?", (fecha, folio))
        # El modelo no tiene un tipo de historial propio para la visita: se registra como corrección de campo.
        eid = _historial(db, folio, quien.id, "Correccion", "fechaVisita", out_dt(r["fecha_visita"]), out_dt(fecha))
        db.execute("INSERT INTO version_correccion (entrada_id) VALUES (?)", (eid,))
        N.al_cambiar_visita(db, _reporte(db, folio))  # RF-15-AC-2
    despachar(db)
    return responder(detalle_para(db, quien, folio), etag=True)


@router.delete("/reports/{folio}/visit")
def cancel_visit(folio: str = FolioP, db=Depends(get_db), quien: UsuarioSesion = Depends(actor)):
    r = visible(db, quien, folio)
    if r["estado"] not in ABIERTOS or r["fecha_visita"] is None:
        raise conflicto("No hay una visita programada que cancelar")
    with tx(db):
        db.execute("UPDATE reporte SET fecha_visita=NULL WHERE folio=?", (folio,))
        eid = _historial(db, folio, quien.id, "Correccion", "fechaVisita", out_dt(r["fecha_visita"]), "Cancelada")
        db.execute("INSERT INTO version_correccion (entrada_id) VALUES (?)", (eid,))
        N.al_cambiar_visita(db, _reporte(db, folio))
    despachar(db)
    return Response(status_code=204)


# ------------------------------------------------------------------ indicaciones de persistencia (RF-19)
def fecha_de_cierre(db, folio: str) -> Optional[str]:
    f = db.execute(
        """SELECT e.fecha FROM entrada_historial e JOIN cambio_estado c ON c.entrada_id=e.id
                      WHERE e.reporte_folio=? AND c.estado_nuevo='Cerrado' ORDER BY e.fecha DESC, e.rowid DESC LIMIT
                          1""",
        (folio,),
    ).fetchone()
    return f["fecha"] if f else None


def dentro_de_plazo_de_reapertura(db, folio: str) -> bool:
    cierre = fecha_de_cierre(db, folio)
    if not cierre:
        return False
    return reloj.ahora() <= reloj.de_texto(cierre) + timedelta(days=parametro(db, "plazoReaperturaDias"))


@router.get("/reports/{folio}/persistence-indications")
def list_persistence_indications(folio: str = FolioP, db=Depends(get_db)):
    _reporte(db, folio)
    filas = db.execute(
        """SELECT e.id, e.fecha, e.comentario, u.nombre AS residente FROM indicacion_persistencia ip
                          JOIN entrada_historial e ON e.id=ip.entrada_id JOIN usuario u ON u.id=ip.residente_id
                          WHERE e.reporte_folio=? ORDER BY e.fecha, e.rowid""",
        (folio,),
    ).fetchall()
    return responder(
        [
            {"id": f["id"], "fecha": out_dt(f["fecha"]), "residente": f["residente"], "comentario": f["comentario"]}
            for f in filas
        ]
    )


@router.post("/reports/{folio}/persistence-indications")
def create_persistence_indication(
    folio: str = FolioP,
    body: Any = Body(default={}),
    idempotency_key: Optional[str] = Header(default=None),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    r = visible(db, quien, folio)
    if r["reportante_id"] != quien.id:
        raise prohibido("Solo el residente reportante indica que el problema persiste")
    if r["estado"] != "Cerrado":
        raise conflicto("Solo se indica la persistencia en un reporte Cerrado")
    if not dentro_de_plazo_de_reapertura(db, folio):
        raise conflicto("El plazo para reabrir terminó")  # RF-19-AC-4
    d = S.parsear(S.PersistenceCreate, body)
    if d.comentario is not None and len(d.comentario) > 1000:
        raise peticion_invalida("El comentario excede 1000 caracteres")  # el YAML no declara 422 en esta operación
    with tx(db):
        eid = _historial(db, folio, quien.id, "PersistenciaIndicada", comentario=d.comentario)
        db.execute("INSERT INTO indicacion_persistencia (entrada_id, residente_id) VALUES (?,?)", (eid, quien.id))
        N._registrar(
            db,
            folio,
            "PersistenciaIndicada",
            f"El residente indicó que el problema de {folio} persiste. Decida si lo reabre.",
            f"ReportaYa: {folio} sigue fallando",
            N.administracion(db),
        )
    despachar(db)
    f = db.execute("SELECT fecha, comentario FROM entrada_historial WHERE id=?", (eid,)).fetchone()
    return responder(
        {"id": eid, "fecha": out_dt(f["fecha"]), "residente": quien.nombre, "comentario": f["comentario"]},
        201,
        f"/reports/{folio}/persistence-indications/{eid}",
    )
