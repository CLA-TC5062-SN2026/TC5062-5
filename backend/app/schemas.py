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
MotivoDetencion = Literal["AccesoAlDepartamento", "EsperaDeProveedor", "EsperaDePieza",
                          "EsperaDeAutorizacionDeGasto", "Otro"]
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
    esPeligroso: bool
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


_MSG = {
    "missing": "Campo obligatorio",
    "string_too_short": "No puede estar vacío o es demasiado corto",
    "literal_error": "Valor no permitido",
}


def parsear(modelo: type[BaseModel], data: Any):
    """Valida el cuerpo. JSON de otro tipo o tipos erróneos -> 400; reglas de valor -> 422."""
    if not isinstance(data, dict):
        raise peticion_invalida("El cuerpo debe ser un objeto JSON")
    try:
        return modelo.model_validate(data)
    except ValidationError as e:
        errores = e.errors()
        if any(x["type"].endswith("_type") or x["type"] in ("extra_forbidden", "bool_type", "int_type")
               for x in errores):
            raise peticion_invalida("Tipo de dato incorrecto o campo desconocido: " +
                                    ", ".join(".".join(map(str, x["loc"])) for x in errores))
        raise ApiError(422, "VALIDACION", "Datos inválidos", [
            {"campo": ".".join(map(str, x["loc"])) or "cuerpo",
             "mensaje": _MSG.get(x["type"], x["msg"].removeprefix("Value error, "))} for x in errores])


def no_vacio(valor: Optional[str], campo: str) -> str:
    if valor is None or not valor.strip():
        raise validacion(campo, "No puede estar vacío")
    return valor.strip()
