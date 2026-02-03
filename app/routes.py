from flask import Blueprint, request, jsonify

from .db import connect

bp = Blueprint("routes", __name__)


@bp.get("/health")
def health():
    """
    Health check: verifies DB is reachable and the dishes table is queryable.
    Returns 200 OK if DB works; 500 if not.
    """
    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.execute("SELECT COUNT(*) AS n FROM dishes;")
            _ = cur.fetchone()
        return "OK", 200
    except Exception as e:
        return f"DB ERROR: {e}", 500


@bp.get("/")
def home():
    """
    Simple HTML page listing dishes.
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT dish, country FROM dishes ORDER BY id;")
        rows = cur.fetchall()

    items = "".join(f"<li>{r['dish']} - {r['country']}</li>" for r in rows)
    return f"""
    <h1>My favorite dishes worldwide</h1>
    <ul>{items}</ul>
    """


@bp.get("/dishes")
def view_dishes():
    """
    Returns all dishes as JSON.
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, dish, country FROM dishes ORDER BY id;")
        rows = cur.fetchall()

    # sqlite3.Row isn't JSON-serializable by default -> convert to dicts
    return jsonify([dict(r) for r in rows]), 200


@bp.post("/dishes")
def add_dish():
    """
    Adds a dish:
    Expected JSON: {"id": 4, "dish": "pizza", "country": "Italy"}
    """
    data = request.get_json(silent=True) or {}

    # Validate required fields
    if "id" not in data:
        return jsonify(error="Missing field: id"), 400

    dish = (data.get("dish") or "").strip()
    country = (data.get("country") or "").strip()

    if not dish:
        return jsonify(error="Missing or empty field: dish"), 400
    if not country:
        return jsonify(error="Missing or empty field: country"), 400

    try:
        dish_id = int(data["id"])
    except (TypeError, ValueError):
        return jsonify(error="Field 'id' must be an integer"), 400

    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO dishes (id, dish, country) VALUES (?, ?, ?);",
                (dish_id, dish, country),
            )
            conn.commit()
    except Exception as e:
        # Most common: UNIQUE constraint failed on id
        return jsonify(error=f"DB ERROR: {e}"), 400

    return jsonify(status="ADDED", id=dish_id, dish=dish, country=country), 201


@bp.delete("/dishes/<int:dish_id>")
def delete_dish(dish_id: int):
    """
    Deletes a dish by id.
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM dishes WHERE id = ?;", (dish_id,))
        conn.commit()
        deleted = cur.rowcount

    if deleted == 0:
        return jsonify(error="Not found"), 404
    return jsonify(status="DELETED", id=dish_id), 200
