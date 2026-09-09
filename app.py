"""
ACEest Fitness & Gym - Flask Web Application
----------------------------------------------
This module exposes the core client-management logic of the ACEest
Fitness & Gym system (originally a Tkinter desktop prototype) as a
lightweight Flask web service so that it can be version-controlled,
unit-tested, containerised, and pushed through a CI/CD pipeline.

Business rules preserved from the desktop prototype:
    * Every client is enrolled in exactly one training program.
    * Each program carries a "calorie factor" used to estimate the
      client's daily calorie target:  calories = weight_kg * factor
    * Weekly adherence (0-100 %) can be logged for each client and
      retrieved later to build a progress history.
"""

from flask import Flask, jsonify, request

# ---------------------------------------------------------------------
# Program catalogue (kept in code so it is trivially unit-testable;
# in a production system this would live in a database/config table).
# ---------------------------------------------------------------------
PROGRAMS = {
    "Fat Loss (FL)": {"calorie_factor": 22},
    "Muscle Gain (MG)": {"calorie_factor": 35},
    "Beginner (BG)": {"calorie_factor": 26},
}


def create_app(testing: bool = False) -> Flask:
    """
    Application factory.

    Using a factory (instead of a bare module-level `app`) makes the
    application trivially testable: pytest can spin up a fresh app
    instance, with its own in-memory data store, for every test run
    without any shared/global state leaking between tests.
    """
    app = Flask(__name__)
    app.config["TESTING"] = testing

    # In-memory "database". Swapping this for SQLAlchemy/SQLite is a
    # drop-in change; keeping it simple here keeps the unit tests fast
    # and avoids filesystem/DB dependencies inside the CI container.
    clients = {}

    # -------------------------------------------------------------
    # Health check - used by Docker HEALTHCHECK / load balancers
    # -------------------------------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        return jsonify(
            {
                "service": "ACEest Fitness & Gym API",
                "status": "running",
                "version": "1.0.0",
            }
        ), 200

    # -------------------------------------------------------------
    # Programs
    # -------------------------------------------------------------
    @app.route("/programs", methods=["GET"])
    def list_programs():
        return jsonify(PROGRAMS), 200

    # -------------------------------------------------------------
    # Clients
    # -------------------------------------------------------------
    @app.route("/clients", methods=["GET"])
    def list_clients():
        return jsonify(list(clients.values())), 200

    @app.route("/clients", methods=["POST"])
    def add_client():
        data = request.get_json(silent=True) or {}

        name = data.get("name")
        age = data.get("age")
        weight = data.get("weight")
        program = data.get("program")

        # ---- validation -------------------------------------------------
        if not name or not isinstance(name, str):
            return jsonify({"error": "A valid client 'name' is required."}), 400

        if program not in PROGRAMS:
            return jsonify(
                {
                    "error": f"Invalid program '{program}'. "
                    f"Valid options: {list(PROGRAMS.keys())}"
                }
            ), 400

        try:
            weight = float(weight)
            age = int(age)
            if weight <= 0 or age <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify(
                {"error": "'age' must be a positive int and 'weight' a positive number."}
            ), 400

        if name in clients:
            return jsonify({"error": f"Client '{name}' already exists."}), 409

        calories = calculate_calories(weight, program)

        clients[name] = {
            "name": name,
            "age": age,
            "weight": weight,
            "program": program,
            "calories": calories,
            "progress": [],
        }
        return jsonify(clients[name]), 201

    @app.route("/clients/<string:name>", methods=["GET"])
    def get_client(name):
        client = clients.get(name)
        if not client:
            return jsonify({"error": f"Client '{name}' not found."}), 404
        return jsonify(client), 200

    @app.route("/clients/<string:name>", methods=["DELETE"])
    def delete_client(name):
        if name not in clients:
            return jsonify({"error": f"Client '{name}' not found."}), 404
        del clients[name]
        return jsonify({"message": f"Client '{name}' deleted."}), 200

    # -------------------------------------------------------------
    # Weekly adherence / progress tracking
    # -------------------------------------------------------------
    @app.route("/clients/<string:name>/progress", methods=["POST"])
    def add_progress(name):
        client = clients.get(name)
        if not client:
            return jsonify({"error": f"Client '{name}' not found."}), 404

        data = request.get_json(silent=True) or {}
        week = data.get("week")
        adherence = data.get("adherence")

        if not week:
            return jsonify({"error": "'week' is required (e.g. 'Week 1')."}), 400

        try:
            adherence = int(adherence)
            if not 0 <= adherence <= 100:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "'adherence' must be an integer between 0 and 100."}), 400

        entry = {"week": week, "adherence": adherence}
        client["progress"].append(entry)
        return jsonify(entry), 201

    @app.route("/clients/<string:name>/progress", methods=["GET"])
    def get_progress(name):
        client = clients.get(name)
        if not client:
            return jsonify({"error": f"Client '{name}' not found."}), 404
        return jsonify(client["progress"]), 200

    return app


def calculate_calories(weight: float, program: str) -> int:
    """Pure helper function - kept outside the Flask routes so it can be
    unit-tested in complete isolation from HTTP/Flask concerns."""
    factor = PROGRAMS[program]["calorie_factor"]
    return int(weight * factor)


# ---------------------------------------------------------------------
# Entry point for local / Docker execution
# ---------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
