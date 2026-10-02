"""
A small Flask API used to demonstrate a complete CI/CD pipeline:
lint -> test -> build Docker image -> push to registry.
"""
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint used by readiness/liveness probes."""
    return jsonify(status="ok"), 200


@app.route("/add", methods=["POST"])
def add():
    """Adds two numbers provided in the JSON body: {"a": 1, "b": 2}."""
    data = request.get_json(silent=True) or {}
    if "a" not in data or "b" not in data:
        return jsonify(error="Both 'a' and 'b' are required"), 400

    try:
        a = float(data["a"])
        b = float(data["b"])
    except (TypeError, ValueError):
        return jsonify(error="'a' and 'b' must be numbers"), 400

    return jsonify(result=a + b), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
