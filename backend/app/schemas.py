"""Modelos de entrada (request) derivados de los schemas del openapi_equipo.yaml.

Los cuerpos se reciben como JSON crudo y se validan DESPUÉS de comprobar que el recurso existe,
para respetar la precedencia de errores del SRS: 404 antes que 422.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from .util import EMAIL_RE, UUID_RE, ApiError, peticion_invalida, validacion
import re

Ocupacion = Literal["Propietario", "Inquilino"]
Rol = Literal["Residente", "Vigilancia", "Mantenimiento", "Administracion"]
Pagador = Literal["Condominio", "Condomino"]
MotivoDetencion = Literal[
    "AccesoAlDepartamento", "EsperaDeProveedor", "EsperaDePieza", "EsperaDeAutorizacionDeGasto", "Otro"
]
MedioOrigen = Literal["Sistema", "WhatsApp", "Llamada", "Caseta", "Correo", "Presencial"]


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def _uuid(v):
    if v is not None and not re.match(UUID_RE, v):
        raise ValueError("Debe ser un UUID")
    return v


def _email(v):
    if v is not None and not EMAIL_RE.match(v):
        raise ValueError("Correo electrónico no válido")
    return v


class Propietario(Base):
    nombre: str
    correo: str
    viveEnCondominio: bool
    v_correo = field_validator("correo")(_email)


class PropietarioPatch(Base):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    viveEnCondominio: Optional[bool] = None
    v_correo = field_validator("correo")(_email)


class UnitCreate(Base):
    torre: str
    piso: int
    numero: str
    propietario: Propietario


class UnitUpdate(Base):
    torre: Optional[str] = None
    piso: Optional[int] = None
    numero: Optional[str] = None
    propietario: Optional[PropietarioPatch] = None
    activa: Optional[bool] = None


class CommonAreaCreate(Base):
    nombre: str


class CommonAreaUpdate(Base):
    nombre: Optional[str] = None
    activa: Optional[bool] = None


class ExternalProviderCreate(Base):
    nombre: str
    especialidad: str
    telefono: str


class ExternalProviderUpdate(Base):
    nombre: Optional[str] = None
    especialidad: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None


class MantenimientoDatos(Base):
    tipo: Literal["PersonalPropio", "ProveedorExterno"]
    especialidad: Optional[str] = None
    telefono: Optional[str] = None


class MantenimientoPatch(Base):
    tipo: Optional[Literal["PersonalPropio", "ProveedorExterno"]] = None
    especialidad: Optional[str] = None
    telefono: Optional[str] = None


class VinculacionCreate(Base):
    unidadId: str
    ocupacion: Ocupacion
    fechaInicio: str
    v_uuid = field_validator("unidadId")(_uuid)


class UserCreate(Base):
    nombre: str
    correo: str
    rol: Rol
    vinculacion: Optional[VinculacionCreate] = None
    mantenimiento: Optional[MantenimientoDatos] = None
    perfilAdministracion: Optional[Literal["Administrador", "Auxiliar"]] = None
    v_correo = field_validator("correo")(_email)


class UserUpdate(Base):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    estadoCuenta: Optional[Literal["Activa", "Desactivada"]] = None
    mantenimiento: Optional[MantenimientoPatch] = None
    v_correo = field_validator("correo")(_email)


class DelegationCreate(Base):
    auxiliarId: str
    fechaFin: Optional[str] = None
    v_uuid = field_validator("auxiliarId")(_uuid)


class DelegationUpdate(Base):
    habilitada: Optional[bool] = None
    fechaFin: Optional[str] = None


class ParameterUpdate(Base):
    valor: float | int


class Ubicacion(Base):
    tipo: Literal["Unidad", "AreaComun"]
    unidadId: Optional[str] = None
    areaComunId: Optional[str] = None
    parteAfectada: Optional[str] = None
    referencia: Optional[str] = None
    v_uuid = field_validator("unidadId", "areaComunId")(_uuid)


class ReportCreate(Base):
    categoriaId: str
    subtipo: Optional[str] = None
    descripcion: str
    ubicacion: Ubicacion
    esPeligroso: Optional[bool] = None  # obligatorio; se valida aparte para dar el mensaje de RF-03-AC-6
    autorizaAcceso: Optional[bool] = None
    horariosAcceso: Optional[str] = None
    desdeCuando: Optional[str] = None
    habiaPasadoAntes: Optional[bool] = None
    medioOrigen: Optional[MedioOrigen] = None
    fechaAviso: Optional[str] = None
    residenteReportanteId: Optional[str] = None
    nombreReferencia: Optional[str] = None
    contactoReferencia: Optional[str] = None
    v_uuid = field_validator("categoriaId", "residenteReportanteId")(_uuid)


class ReportCorrection(Base):
    categoriaId: Optional[str] = None
    subtipo: Optional[str] = None
    descripcion: Optional[str] = None
    ubicacion: Optional[Ubicacion] = None
    v_uuid = field_validator("categoriaId")(_uuid)


class NoteCreate(Base):
    texto: str


class HoldCreate(Base):
    motivo: MotivoDetencion
    textoOtro: Optional[str] = None


class HoldPatch(Base):
    reanudada: Literal[True]


class CostCreate(Base):
    monto: Optional[float | int] = None
    pagador: Pagador
    comentario: Optional[str] = None
    anulaCostoId: Optional[str] = None
    v_uuid = field_validator("anulaCostoId")(_uuid)


class PersistenceCreate(Base):
    comentario: Optional[str] = None


class VisitPut(Base):
    fechaVisita: str


class NotificationPatch(Base):
    leido: Literal[True]


# ---------------------------------------------------------------- flujo de estados (S11)
Prioridad = Literal["Urgente", "Normal", "Menor"]
Responsabilidad = Literal["Comun", "Privada", "PorDeterminar"]


class AssignRequest(Base):
    # prioridad y responsableId son obligatorios; se declaran opcionales para responder con el mensaje del SRS
    # («La prioridad es obligatoria», RF-06-AC-3) en lugar del genérico.
    prioridad: Optional[Prioridad] = None
    responsableId: Optional[str] = None
    ubicacionOrigen: Optional[Ubicacion] = None
    responsabilidad: Optional[Responsabilidad] = None
    responsableCosto: Optional[Pagador] = None
    v_uuid = field_validator("responsableId")(_uuid)


class ReclassifyRequest(Base):
    prioridad: Optional[Prioridad] = None
    responsableId: Optional[str] = None
    ubicacionOrigen: Optional[Ubicacion] = None
    responsabilidad: Optional[Responsabilidad] = None
    responsableCosto: Optional[Pagador] = None
    v_uuid = field_validator("responsableId")(_uuid)


class StartRequest(Base):
    actuaEnNombreDe: Optional[str] = None
    comentario: Optional[str] = None


class CompletionData(Base):
    notaTrabajo: Optional[str] = None
    justificacionSinEvidencia: Optional[str] = None
    garantiaVencimiento: Optional[str] = None
    pendientes: Optional[str] = None


class ResidentResponseCreate(Base):
    respuesta: Literal["YaQuedo", "SigueFallando"]
    comentario: Optional[str] = None


class CloseRequest(Base):
    motivo: Optional[str] = None


class CancelRequest(Base):
    motivo: Optional[str] = None


class CommentRequest(Base):
    comentario: Optional[str] = None


class MergeRequest(Base):
    reportePrincipal: str


class WarrantyPut(Base):
    garantiaVencimiento: str


class ShareCreate(Base):
    proveedorId: str
    consentimientoResidente: Optional[bool] = None
    v_uuid = field_validator("proveedorId")(_uuid)


class TokenPassword(Base):
    token: str
    password: str


class ResetRequest(Base):
    correo: str


_MSG = {
    "missing": "Campo obligatorio",
    "string_too_short": "No puede estar vacío o es demasiado corto",
    "literal_error": "Valor no permitido",
}


# Mensajes del SRS para campos obligatorios ausentes (SRS 3.0: «el mensaje que indica cada criterio»).
MENSAJES_OBLIGATORIO = {
    "piso": "El piso es obligatorio",  # RF-02-AC-6
    "propietario.correo": "El correo del propietario es obligatorio",  # RF-02-AC-5
    "propietario.nombre": "El nombre del propietario es obligatorio",
    "descripcion": "La descripción debe tener entre 10 y 1,000 caracteres",
    "motivo": "Indique el motivo de la detención",  # RF-18-AC-2 (HoldCreate)
    "categoriaId": "Indique la categoría",
    "ubicacion": "Indique la ubicación",
    "correo": "El correo es obligatorio",
    "password": "La contraseña es obligatoria",
    "token": "El enlace no es válido",
    "respuesta": "Indique «Ya quedó» o «Sigue fallando»",
    "fechaVisita": "Indique la fecha de la visita",
    "garantiaVencimiento": "Indique la fecha de vencimiento de la garantía",
    "reportePrincipal": "Indique el reporte principal",
    "proveedorId": "Indique el proveedor",
}


def parsear(modelo: type[BaseModel], data: Any):
    """Valida el cuerpo. JSON de otro tipo o tipos erróneos -> 400; reglas de valor -> 422."""
    if not isinstance(data, dict):
        raise peticion_invalida("El cuerpo debe ser un objeto JSON")
    try:
        return modelo.model_validate(data)
    except ValidationError as e:
        errores = e.errors()
        if any(
            x["type"].endswith("_type") or x["type"] in ("extra_forbidden", "bool_type", "int_type") for x in errores
        ):
            raise peticion_invalida(
                "Tipo de dato incorrecto o campo desconocido: "
                + ", ".join(".".join(map(str, x["loc"])) for x in errores)
            )
        detalle = []
        for x in errores:
            campo = ".".join(map(str, x["loc"])) or "cuerpo"
            if x["type"] == "missing" and campo in MENSAJES_OBLIGATORIO:
                mensaje = MENSAJES_OBLIGATORIO[campo]
            else:
                mensaje = _MSG.get(x["type"], x["msg"].removeprefix("Value error, "))
            detalle.append({"campo": campo, "mensaje": mensaje})
        raise ApiError(422, "VALIDACION", detalle[0]["mensaje"] if len(detalle) == 1 else "Datos inválidos", detalle)


def no_vacio(valor: Optional[str], campo: str) -> str:
    if valor is None or not valor.strip():
        raise validacion(campo, "No puede estar vacío")
    return valor.strip()


# ---------------------------------------------------------------- autenticación (S05-S06-A2)
class Credenciales(Base):
    correo: str
    password: str
