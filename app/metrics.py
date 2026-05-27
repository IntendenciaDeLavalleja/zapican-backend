"""Métricas Prometheus con soporte multiprocess (gunicorn)."""
from __future__ import annotations

import os
import time

from flask import Blueprint, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    multiprocess,
)

metrics_bp = Blueprint("metrics", __name__)

http_requests_total = Counter(
    "http_requests_total",
    "Cantidad total de requests HTTP",
    ["method", "endpoint", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Duracion de los requests HTTP en segundos",
    ["method", "endpoint"],
)


def register_request_hooks(app):
    @app.before_request
    def _start_timer():
        request._metrics_start = time.perf_counter()

    @app.after_request
    def _record(response):
        try:
            elapsed = time.perf_counter() - getattr(request, "_metrics_start", time.perf_counter())
            endpoint = request.endpoint or "unknown"
            http_requests_total.labels(request.method, endpoint, response.status_code).inc()
            http_request_duration_seconds.labels(request.method, endpoint).observe(elapsed)
        except Exception:
            pass
        return response


@metrics_bp.route("", methods=["GET"])
def metrics():
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        from prometheus_client import REGISTRY as registry  # type: ignore
    return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}
