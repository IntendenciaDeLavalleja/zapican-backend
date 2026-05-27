#!/bin/sh
set -e

echo "[entrypoint] Preparando directorio Prometheus en $PROMETHEUS_MULTIPROC_DIR"
rm -rf "$PROMETHEUS_MULTIPROC_DIR"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

if [ "${RUN_DB_UPGRADE:-true}" = "true" ]; then
  attempts="${DB_UPGRADE_RETRIES:-12}"
  delay="${DB_UPGRADE_RETRY_DELAY:-5}"
  count=1

  until flask db upgrade; do
    if [ "$count" -ge "$attempts" ]; then
      echo "[entrypoint] flask db upgrade fallo despues de $attempts intentos"
      exit 1
    fi

    echo "[entrypoint] flask db upgrade fallo; reintentando en ${delay}s ($count/$attempts)"
    count=$((count + 1))
    sleep "$delay"
  done

  echo "[entrypoint] migraciones aplicadas"
fi

if [ "${RUN_BOOTSTRAP_ADMIN:-false}" = "true" ]; then
  echo "[entrypoint] bootstrap admin"
  flask bootstrap-admin || true
fi

echo "[entrypoint] Iniciando Gunicorn"
exec gunicorn -w "${GUNICORN_WORKERS:-4}" -k gthread \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --graceful-timeout 30 --keep-alive 5 \
  --log-level "${GUNICORN_LOG_LEVEL:-info}" \
  -b 0.0.0.0:5000 "wsgi:app"
