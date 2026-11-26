# Imagen del API de ReportaYa (FastAPI + SQLite). Los datos viven en el volumen /data.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/reportaya.db \
    UPLOAD_DIR=/data/uploads \
    CORREO_BANDEJA_DIR=/data/correos

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY db ./db
COPY scripts ./scripts
COPY openapi_equipo.yaml ./
COPY docker-entrypoint.sh /usr/local/bin/

# Usuario sin privilegios; /data se monta como volumen persistente.
RUN useradd --create-home --uid 1000 reportaya && mkdir -p /data /respaldos && chown reportaya /data /respaldos \
    && chmod +x /usr/local/bin/docker-entrypoint.sh
USER reportaya

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
ENTRYPOINT ["docker-entrypoint.sh"]
# Un solo proceso: la tarea periódica (reintentos de correo, RF-22) corre dentro del servidor y SQLite admite un escritor.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
