"""Fotos y video de los reportes (RF-05, RD-08, RNF-15).

Se listan y descargan según la matriz de visibilidad; ningún archivo se borra (RNF-07, RF-05-AC-7: 403 para
todos los roles, también la Administración). La Administración deja constancia de cada foto que comparte con
un proveedor sin acceso (RNF-15).
"""

from typing import Any

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import Response
from urllib.parse import quote

from .. import schemas as S
from ..almacen import ArchivoNoEncontrado, almacen
from .. import visibilidad as V
from ..db import get_db, tx
from ..security import UsuarioSesion, actor
from ..serial import file_out
from ..util import FOLIO_RE, UUID_RE, new_id, no_encontrado, now_utc, out_dt, prohibido, responder, validacion
from .reportes import visible

router = APIRouter()
FolioP = Path(..., pattern=FOLIO_RE)
FileP = Path(..., pattern=UUID_RE)
TIPOS = {"jpeg": "image/jpeg", "jpg": "image/jpeg", "png": "image/png", "mp4": "video/mp4"}


def _adjunto(db, folio: str, file_id: str):
    a = db.execute("SELECT * FROM adjunto WHERE id=? AND reporte_folio=?", (file_id, folio)).fetchone()
    if not a:
        raise no_encontrado("Archivo no encontrado")
    return a


@router.get("/reports/{folio}/files")
def list_files(folio: str = FolioP, db=Depends(get_db), quien: UsuarioSesion = Depends(actor)):
    r = visible(db, quien, folio)
    filas = db.execute(
        "SELECT * FROM adjunto WHERE reporte_folio=? ORDER BY etapa, ciclo_numero, fecha, rowid", (folio,)
    ).fetchall()
    return responder([file_out(a, folio) for a in filas if V.archivo_visible(db, quien, r, a)])


@router.get("/reports/{folio}/files/{fileId}")
def download_file(folio: str = FolioP, fileId: str = FileP, db=Depends(get_db), quien: UsuarioSesion = Depends(actor)):
    r = visible(db, quien, folio)
    a = _adjunto(db, folio, fileId)
    if not V.archivo_visible(db, quien, r, a):
        raise no_encontrado("Archivo no encontrado")
    try:
        contenido = almacen().leer(a["clave"])
    except ArchivoNoEncontrado:
        raise no_encontrado("Archivo no encontrado")
    nombre = quote(a["nombre"])
    return Response(
        contenido,
        media_type=TIPOS.get(a["formato"], "application/octet-stream"),
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{nombre}", "Cache-Control": "private, max-age=3600"},
    )


@router.delete("/reports/{folio}/files/{fileId}")
def delete_file_rejected(folio: str = FolioP, fileId: str = FileP):
    raise prohibido("Las fotografías y videos no se borran (RNF-07)")


@router.post("/reports/{folio}/files/{fileId}/shares")
def share_file(
    folio: str = FolioP,
    fileId: str = FileP,
    body: Any = Body(...),
    db=Depends(get_db),
    quien: UsuarioSesion = Depends(actor),
):
    visible(db, quien, folio)
    a = _adjunto(db, folio, fileId)
    d = S.parsear(S.ShareCreate, body)
    if not db.execute("SELECT 1 FROM proveedor_sin_acceso WHERE id=?", (d.proveedorId,)).fetchone():
        raise validacion("proveedorId", "El proveedor sin acceso no existe")
    sid = new_id()
    with tx(db):
        db.execute(
            """INSERT INTO registro_comparticion (id, archivo_id, proveedor_id, registrada_por, fecha,
                      consentimiento_residente) VALUES (?,?,?,?,?,?)""",
            (
                sid,
                a["id"],
                d.proveedorId,
                quien.id,
                now_utc(),
                None if d.consentimientoResidente is None else int(d.consentimientoResidente),
            ),
        )
    f = db.execute("SELECT * FROM registro_comparticion WHERE id=?", (sid,)).fetchone()
    return responder(
        {
            "id": f["id"],
            "archivoId": f["archivo_id"],
            "proveedorId": f["proveedor_id"],
            "consentimientoResidente": None
            if f["consentimiento_residente"] is None
            else bool(f["consentimiento_residente"]),
            "fecha": out_dt(f["fecha"]),
        },
        201,
        f"/reports/{folio}/files/{fileId}/shares/{sid}",
    )
