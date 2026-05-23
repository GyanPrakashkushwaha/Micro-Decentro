from functools import wraps
from flask import request, jsonify

API_KEY = "decentro-secret-key-2026"

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_KEY:
            return jsonify({"message": "Invalid or missing API Key"}), 401
        return f(*args, **kwargs)
    return decorated
