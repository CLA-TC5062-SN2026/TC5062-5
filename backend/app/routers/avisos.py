"""Avisos en el sistema y bitácora de correos (RF-11)."""
from typing import Any, Literal, Optional

from fastapi import APIRouter, Body, Depends, Path, Query

from .. import schemas as S
from ..db import get_db, tx
from ..serial import b
from ..util import FOLIO_RE, UUID_RE, no_encontrado, out_dt, pagina, paginacion, responder
from ..security import actor

router = APIRouter()


def _notif(r) -> dict:
    return {"id": r["id"], "evento": r["evento"], "folio": r["reporte_folio"], "mensaje": r["mensaje"],
            "fecha": out_dt(r["fecha"]), "leido": b(r["leido"])}


NOTIF_SEL = "a.id, a.evento, a.reporte_folio, a.fecha, s.mensaje, s.leido"
NOTIF_FROM = "FROM aviso a JOIN aviso_sistema s ON s.aviso_id = a.id"


@router.get("/notifications")
def list_notifications(leido: Optional[bool] = None, db=Depends(get_db), pg=Depends(paginacion), quien=Depends(actor)):
    where, params = " WHERE s.destinatario_usuario_id = ?", [quien["id"]]
    if leido is not None:
        where += " AND s.leido = ?"; params.append(int(leido))
    return responder(pagina(db, NOTIF_FROM + where, params, NOTIF_SEL, "a.fecha DESC, a.rowid DESC", pg, _notif))


@router.patch("/notifications/{notificationId}")
def mark_notification_read(notificationId: str = Path(..., pattern=UUID_RE), body: Any = Body(...), db=Depends(get_db),
                           quien=Depends(actor)):
    fila = db.execute(f"SELECT {NOTIF_SEL} {NOTIF_FROM} WHERE a.id=? AND s.destinatario_usuario_id=?",
                      (notificationId, quien["id"])).fetchone()
    if not fila:  # inexistente o de otro usuario: no se distingue
        raise no_encontrado("Aviso no encontrado")
    S.parsear(S.NotificationPatch, body)
    with tx(db):
        db.execute("UPDATE aviso_sistema SET leido=1 WHERE aviso_id=?", (notificationId,))
    fila = db.execute(f"SELECT {NOTIF_SEL} {NOTIF_FROM} WHERE a.id=?", (notificationId,)).fetchone()
    return responder(_notif(fila))


@router.get("/email-deliveries")
def list_email_deliveries(estado: Optional[Literal["Pendiente", "Enviado", "Fallido"]] = None,
                          folio: Optional[str] = Query(None, pattern=FOLIO_RE), db=Depends(get_db), pg=Depends(paginacion)):
    where, params = [], []
    if estado:
        where.append("e.estado=?"); params.append(estado)
    if folio:
        where.append("a.reporte_folio=?"); params.append(folio)
    sql_from = "FROM aviso a JOIN envio_correo e ON e.aviso_id = a.id" + (" WHERE " + " AND ".join(where) if where else "")
    return responder(pagina(db, sql_from, params, "a.id, a.reporte_folio, a.evento, a.fecha, e.destinatario, e.estado, e.intentos",
                            "a.fecha DESC, a.rowid DESC", pg,
                            lambda r: {"id": r["id"], "folio": r["reporte_folio"], "destinatario": r["destinatario"],
                                       "evento": r["evento"], "estado": r["estado"], "intentos": r["intentos"],
                                       "fecha": out_dt(r["fecha"])}))
