from flask import g, jsonify


def current_request_id():
    return getattr(
        g,
        "request_id",
        None
    )


def error_response(
    message,
    status_code=400,
    code="request_error",
    details=None
):
    payload = {
        "error": str(message),
        "code": code,
        "request_id": current_request_id()
    }

    if details:
        payload["details"] = str(details)

    return jsonify(payload), status_code
