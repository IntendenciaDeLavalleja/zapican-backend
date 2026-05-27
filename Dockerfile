FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
  FLASK_APP=wsgi.py \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc_dir

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libmariadb-dev pkg-config libmagic1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:5000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
