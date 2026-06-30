import time

from flask import (
    Blueprint,
    current_app,
    jsonify
)

from services.health_service import (
    get_system_health
)
from services.telemetry_service import record_health_event


health_routes = Blueprint(
    "health_routes",
    __name__
)


def _checked_health():
    started = time.perf_counter()
    result = get_system_health(current_app.config)
    duration_ms = (time.perf_counter() - started) * 1000
    record_health_event(
        result,
        duration_ms=duration_ms,
        minimum_interval_seconds=current_app.config.get(
            "HEALTH_HISTORY_INTERVAL_SECONDS",
            300,
        ),
    )
    return result


@health_routes.route(
    "/api/health/live",
    methods=["GET"]
)
def liveness():
    return jsonify({
        "status": "alive"
    })


@health_routes.route(
    "/api/health",
    methods=["GET"]
)
def health():
    return jsonify(_checked_health())


@health_routes.route(
    "/api/health/ready",
    methods=["GET"]
)
def readiness():
    result = _checked_health()
    status_code = 200 if result["ready"] else 503
    return jsonify(result), status_code
