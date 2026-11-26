"""Serialización de filas SQLite a los schemas del API (nombres de campo EXACTOS del YAML)."""
from . import config
from .util import out_dt


def b(x):
    return None if x is None else bool(x)


# ----------------------------------------------------------- unidades y áreas
UNIT_SQL = """SELECT u.ubicacion_id AS id, u.torre, u.piso, u.numero, u.propietario_nombre,
              u.propietario_correo, u.propietario_vive_en_condominio, b.activa
              FROM unidad u JOIN ubicacion b ON b.id = u.ubicacion_id"""
AREA_SQL = "SELECT a.ubicacion_id AS id, a.nombre, b.activa FROM area_comun a JOIN ubicacion b ON b.id = a.ubicacion_id"


def unit_out(r) -> dict:
    return {"id": r["id"], "torre": r["torre"], "piso": r["piso"], "numero": r["numero"],
            "etiqueta": f"{r['torre']}-{r['numero']}", "activa": b(r["activa"]),
            "propietario": {"nombre": r["propietario_nombre"], "correo": r["propietario_correo"],
                            "viveEnCondominio": b(r["propietario_vive_en_condominio"])}}


def area_out(r) -> dict:
    return {"id": r["id"], "nombre": r["nombre"], "activa": b(r["activa"])}


def provider_out(r) -> dict:
    return {"id": r["id"], "nombre": r["nombre"], "especialidad": r["especialidad"],
            "telefono": r["telefono"], "activo": b(r["activo"])}


def vinculacion_out(db, r) -> dict:
    unidad = db.execute(UNIT_SQL + " WHERE u.ubicacion_id = ?", (r["unidad_id"],)).fetchone()
    return {"id": r["id"], "unidad": unit_out(unidad), "ocupacion": r["ocupacion"],
            "fechaInicio": out_dt(r["fecha_inicio"]), "fechaFin": out_dt(r["fecha_fin"])}


def user_out(db, r) -> dict:
    d = {"id": r["id"], "nombre": r["nombre"], "correo": r["correo"], "rol": r["rol"],
         "estadoCuenta": r["estado_cuenta"]}
    if r["rol"] == "Residente":
        v = db.execute("SELECT * FROM vinculacion_unidad WHERE residente_id=? AND fecha_fin IS NULL", (r["id"],)).fetchone()
        if v:
            d["vinculacion"] = vinculacion_out(db, v)
    elif r["rol"] == "Mantenimiento":
        m = db.execute("SELECT * FROM usuario_mantenimiento WHERE usuario_id=?", (r["id"],)).fetchone()
        if m:
            d["mantenimiento"] = {"tipo": m["tipo"], "especialidad": m["especialidad"], "telefono": m["telefono"]}
    elif r["rol"] == "Administracion":
        a = db.execute("SELECT perfil_administracion FROM usuario_administracion WHERE usuario_id=?", (r["id"],)).fetchone()
        if a:
            d["perfilAdministracion"] = a["perfil_administracion"]
    return d


def delegation_out(r) -> dict:
    return {"id": r["id"], "auxiliarId": r["auxiliar_id"], "habilitada": b(r["habilitada"]),
            "fechaInicio": out_dt(r["fecha_inicio"]), "fechaFin": out_dt(r["fecha_fin"])}


def parameter_out(r) -> dict:
    return {"clave": r["clave"], "descripcion": r["descripcion"], "valor": r["valor"], "unidad": r["unidad"]}


# ----------------------------------------------------------- reportes
def etiqueta(db, ubicacion_id: str) -> str:
    f = db.execute("SELECT etiqueta FROM v_ubicacion WHERE id=?", (ubicacion_id,)).fetchone()
    return f["etiqueta"] if f else None


def ubicacion_out(db, ubicacion_id, parte=None, referencia=None) -> dict | None:
    if ubicacion_id is None:
        return None
    t = db.execute("SELECT tipo FROM ubicacion WHERE id=?", (ubicacion_id,)).fetchone()["tipo"]
    d = {"tipo": t}
    d["unidadId" if t == "Unidad" else "areaComunId"] = ubicacion_id
    d["parteAfectada"], d["referencia"] = parte, referencia
    d["etiqueta"] = etiqueta(db, ubicacion_id)
    return d


def file_out(r, folio) -> dict:
    return {"id": r["id"], "tipo": r["tipo"], "etapa": r["etapa"], "ciclo": r["ciclo_numero"],
            "nombre": r["nombre"], "fecha": out_dt(r["fecha"]),
            "url": f"{config.API_PREFIX}/reports/{folio}/files/{r['id']}"}


def hold_out(db, r) -> dict:
    autor = db.execute("SELECT nombre FROM usuario WHERE id=?", (r["autor_id"],)).fetchone()["nombre"]
    return {"id": r["id"], "motivo": r["motivo"], "textoOtro": r["texto_otro"],
            "fechaInicio": out_dt(r["fecha_inicio"]), "fechaFin": out_dt(r["fecha_fin"]), "autor": autor}


COST_SQL = """SELECT e.id, e.fecha, e.comentario, u.nombre AS autor, c.monto, c.pagador, c.anula_costo_id,
              EXISTS (SELECT 1 FROM costo c2 WHERE c2.anula_costo_id = c.entrada_id) AS anulada
              FROM costo c JOIN entrada_historial e ON e.id = c.entrada_id JOIN usuario u ON u.id = e.autor_id
              WHERE e.reporte_folio = ? ORDER BY e.fecha, e.rowid"""


def cost_out(r) -> dict:
    return {"id": r["id"], "monto": r["monto"], "pagador": r["pagador"], "comentario": r["comentario"],
            "anulaCostoId": r["anula_costo_id"], "fecha": out_dt(r["fecha"]), "autor": r["autor"],
            "anulada": b(r["anulada"])}


NOTE_SQL = """SELECT e.id, n.texto, u.nombre AS autor, e.fecha FROM nota_avance n
              JOIN entrada_historial e ON e.id = n.entrada_id JOIN usuario u ON u.id = e.autor_id
              WHERE e.reporte_folio = ? ORDER BY e.fecha, e.rowid"""


def note_out(r) -> dict:
    return {"id": r["id"], "texto": r["texto"], "autor": r["autor"], "fecha": out_dt(r["fecha"])}


def responsable_out(db, r) -> dict | None:
    if r["responsable_usuario_id"]:
        f = db.execute("""SELECT u.id, u.nombre, m.tipo, m.especialidad FROM usuario u
                          JOIN usuario_mantenimiento m ON m.usuario_id = u.id WHERE u.id=?""",
                       (r["responsable_usuario_id"],)).fetchone()
        return {"id": f["id"], "tipo": f["tipo"], "nombre": f["nombre"], "especialidad": f["especialidad"], "sinAcceso": False}
    if r["responsable_proveedor_id"]:
        f = db.execute("SELECT * FROM proveedor_sin_acceso WHERE id=?", (r["responsable_proveedor_id"],)).fetchone()
        return {"id": f["id"], "tipo": "ProveedorExterno", "nombre": f["nombre"], "especialidad": f["especialidad"], "sinAcceso": True}
    return None


def report_summary(db, r) -> dict:
    cat = db.execute("SELECT nombre FROM categoria WHERE id=?", (r["categoria_id"],)).fetchone()["nombre"]
    detenido = db.execute("SELECT 1 FROM detencion WHERE reporte_folio=? AND fecha_fin IS NULL", (r["folio"],)).fetchone()
    return {"folio": r["folio"], "estado": r["estado"], "prioridad": r["prioridad"], "categoria": cat,
            "subtipo": r["subtipo_nombre"], "descripcion": r["descripcion"],
            "ubicacion": ubicacion_out(db, r["ubicacion_id"], r["parte_afectada"], r["referencia"]),
            "fechaAviso": out_dt(r["fecha_aviso"]), "detenido": detenido is not None,
            "posibleDuplicado": r["posible_duplicado_de"] is not None}


def report_detail(db, r) -> dict:
    folio = r["folio"]
    d = report_summary(db, r)
    if r["reportante_id"]:
        nombre = db.execute("SELECT nombre FROM usuario WHERE id=?", (r["reportante_id"],)).fetchone()["nombre"]
        reportante = {"id": r["reportante_id"], "nombre": nombre, "sinCuenta": False}
    else:
        reportante = {"nombre": r["nombre_referencia"], "sinCuenta": True}
    cap = db.execute("SELECT id, nombre FROM usuario WHERE id=?", (r["capturado_por"],)).fetchone()
    costos = [cost_out(c) for c in db.execute(COST_SQL, (folio,)).fetchall()]
    vigentes = [c for c in costos if not c["anulada"]]
    ultimo = vigentes[-1] if vigentes else None
    abierta = db.execute("SELECT * FROM detencion WHERE reporte_folio=? AND fecha_fin IS NULL", (folio,)).fetchone()
    ciclos = []
    fila_ciclos = db.execute("SELECT * FROM ciclo_atencion WHERE reporte_folio=? ORDER BY numero", (folio,)).fetchall()
    for c in fila_ciclos:
        fotos = db.execute("SELECT * FROM adjunto WHERE reporte_folio=? AND ciclo_numero=? ORDER BY fecha, rowid",
                           (folio, c["numero"])).fetchall()
        conf = db.execute("SELECT * FROM confirmacion_residente WHERE reporte_folio=? AND ciclo_numero=?",
                          (folio, c["numero"])).fetchone()
        ciclos.append({"numero": c["numero"], "inicio": out_dt(c["inicio"]), "fin": out_dt(c["fin"]),
                       "fotosEvidencia": [file_out(f, folio) for f in fotos],
                       "notaTrabajo": c["nota_trabajo"], "pendientes": c["pendientes"],
                       "sinEvidenciaFotografica": b(c["sin_evidencia_fotografica"]),
                       "justificacionSinEvidencia": c["justificacion_sin_evidencia"],
                       "garantiaVencimiento": c["garantia_vencimiento"],
                       "confirmacion": ({"respuesta": conf["respuesta"], "comentario": conf["comentario"],
                                         "fecha": out_dt(conf["fecha"])} if conf else None),
                       "plazoConfirmacionHasta": out_dt(c["plazo_confirmacion_hasta"])})
    fotos_alta = db.execute("SELECT * FROM adjunto WHERE reporte_folio=? AND etapa='Alta' ORDER BY fecha, rowid", (folio,)).fetchall()
    unidad = db.execute(UNIT_SQL + " WHERE u.ubicacion_id=?", (r["ubicacion_id"],)).fetchone()
    d.update({
        "ubicacionOrigen": ubicacion_out(db, r["ubicacion_origen_id"]),
        "medioOrigen": r["medio_origen"], "esPeligroso": b(r["es_peligroso"]),
        "prioridadSugerida": r["prioridad_sugerida"], "responsabilidad": r["responsabilidad"],
        "responsableCosto": r["responsable_costo"], "responsable": responsable_out(db, r),
        "reportante": reportante, "capturadoPor": {"id": cap["id"], "nombre": cap["nombre"]},
        "fechaCaptura": out_dt(r["fecha_captura"]),
        "propietario": unit_out(unidad)["propietario"] if unidad else None,
        "autorizaAcceso": b(r["autoriza_acceso"]), "horariosAcceso": r["horarios_acceso"],
        "desdeCuando": r["desde_cuando"], "habiaPasadoAntes": b(r["habia_pasado_antes"]),
        "fechaVisita": out_dt(r["fecha_visita"]),
        "detencionAbierta": hold_out(db, abierta) if abierta else None,
        "reportePrincipal": r["reporte_principal"],
        "montoCosto": ultimo["monto"] if ultimo else None, "pagador": ultimo["pagador"] if ultimo else None,
        "notas": [note_out(n) for n in db.execute(NOTE_SQL, (folio,)).fetchall()],
        "fotosAlta": [file_out(f, folio) for f in fotos_alta], "ciclos": ciclos,
        "reaperturas": max(len(ciclos) - 1, 0)})
    return d
