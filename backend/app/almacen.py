"""Almacenamiento de fotos y videos intercambiable (RNF-08, R-05: patrón Adapter).

Las reglas de negocio solo conocen la interfaz `AlmacenArchivos`. La implementación se elige con `ALMACEN`
en `.env`: `local` (carpeta `UPLOAD_DIR`) o `s3` (cualquier servicio compatible con S3: AWS S3, Cloudflare R2,
MinIO). Cambiar de una a otra no toca ningún router. Corrige la deuda DIP del code review de S09-A1.

`borrar` existe solo para deshacer archivos escritos en una operación que después falló (compensación);
ningún endpoint permite borrar una foto (RNF-07, RF-05-AC-7).
"""

from pathlib import Path
from typing import Protocol

from . import config


class ArchivoNoEncontrado(Exception):
    pass


class AlmacenArchivos(Protocol):
    def guardar(self, clave: str, contenido: bytes, tipo_mime: str) -> None: ...
    def leer(self, clave: str) -> bytes: ...
    def borrar(self, clave: str) -> None: ...


class AlmacenLocal:
    def __init__(self, carpeta: Path):
        self.carpeta = carpeta

    def _ruta(self, clave: str) -> Path:
        ruta = (self.carpeta / clave).resolve()
        if self.carpeta.resolve() not in ruta.parents:  # nunca fuera de la carpeta (claves con «..»)
            raise ArchivoNoEncontrado(clave)
        return ruta

    def guardar(self, clave: str, contenido: bytes, tipo_mime: str) -> None:
        ruta = self._ruta(clave)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(contenido)

    def leer(self, clave: str) -> bytes:
        ruta = self._ruta(clave)
        if not ruta.is_file():
            raise ArchivoNoEncontrado(clave)
        return ruta.read_bytes()

    def borrar(self, clave: str) -> None:
        self._ruta(clave).unlink(missing_ok=True)


class AlmacenS3:
    """S3 o compatible. Credenciales por la cadena estándar de boto3 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)."""

    def __init__(
        self, bucket: str, prefijo: str = "", endpoint_url: str | None = None, region: str | None = None, cliente=None
    ):
        if not bucket:
            raise RuntimeError("Con ALMACEN=s3 defina S3_BUCKET en .env")
        if cliente is None:
            import boto3  # solo se necesita con ALMACEN=s3

            cliente = boto3.client("s3", endpoint_url=endpoint_url or None, region_name=region or None)
        self.s3, self.bucket, self.prefijo = cliente, bucket, prefijo.strip("/")

    def _clave(self, clave: str) -> str:
        return f"{self.prefijo}/{clave}" if self.prefijo else clave

    def guardar(self, clave: str, contenido: bytes, tipo_mime: str) -> None:
        self.s3.put_object(Bucket=self.bucket, Key=self._clave(clave), Body=contenido, ContentType=tipo_mime)

    def leer(self, clave: str) -> bytes:
        try:
            return self.s3.get_object(Bucket=self.bucket, Key=self._clave(clave))["Body"].read()
        except self.s3.exceptions.NoSuchKey as exc:
            raise ArchivoNoEncontrado(clave) from exc

    def borrar(self, clave: str) -> None:
        self.s3.delete_object(Bucket=self.bucket, Key=self._clave(clave))


_almacen: AlmacenArchivos | None = None


def almacen() -> AlmacenArchivos:
    global _almacen
    if _almacen is None:
        if config.ALMACEN == "local":
            _almacen = AlmacenLocal(config.UPLOAD_DIR)
        elif config.ALMACEN == "s3":
            _almacen = AlmacenS3(config.S3_BUCKET, config.S3_PREFIJO, config.S3_ENDPOINT_URL, config.S3_REGION)
        else:
            raise RuntimeError(f"ALMACEN={config.ALMACEN!r} no es válido: use 'local' o 's3'")
    return _almacen


def usar(otro: AlmacenArchivos | None) -> None:
    """Sustituye el almacén (pruebas). None vuelve al configurado."""
    global _almacen
    _almacen = otro
