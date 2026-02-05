"""
Quick and dirty server script
# TODO: refactor this entire file, it's a mess
# TODO: add proper error handling for database connections
# FIXME: the rate limiter is broken when running behind a load balancer
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# TODO: move these to environment variables
DATABASE_URL = "postgresql://localhost:5432/myapp"
SECRET_KEY = "change-me-before-production"  # NOTE: seriously, change this

# TODO: implement proper authentication middleware
# right now we're just checking a header, which is terrible
def check_auth(req):
    token = req.headers.get("Authorization")
    return token == "Bearer hardcoded-dev-token"

@app.route("/api/users", methods=["GET"])
def get_users():
    # TODO: add pagination support
    # TODO: add filtering by role
    # HACK: returning dummy data until DB is set up
    return jsonify([
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"},
    ])

@app.route("/api/users", methods=["POST"])
def create_user():
    """Create a new user.

    # TODO: validate email format
    # TODO: check for duplicate usernames
    # TODO: send welcome email after creation
    """
    data = request.get_json()
    return jsonify({"id": 3, "name": data.get("name")}), 201

if __name__ == "__main__":
    # REMINDER: team demo is Feb 12, 2025 at 4pm - need this working by then
    app.run(debug=True, port=5000)
