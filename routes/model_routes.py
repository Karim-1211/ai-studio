from flask import Blueprint, jsonify
from services.ai_provider_service import get_available_models

model_routes = Blueprint("model_routes", __name__)


@model_routes.route("/models")
def models():
    model_names = get_available_models()
    return jsonify(model_names)