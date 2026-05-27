"""Blueprint API."""
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/v1")

from app.api import public  # noqa: E402,F401
