from flask import jsonify, Blueprint
from app.models import Exercise_Library
from app.utils.db_helpers import get_all_items, get_item_by_id

bp = Blueprint('exercises', __name__)

# ----------------------------------------- Exercises -----------------------------------------

# Retrieve exercises
@bp.route('/', methods=['GET'])
def get_exercise_list():
    result = get_all_items(Exercise_Library)
    return jsonify({"status": "success", "exercises": result}), 200

# Show exercises based on id.
@bp.route('/<exercise_id>', methods=['GET'])
def read_exercise(exercise_id):
    result = get_item_by_id(Exercise_Library, exercise_id)
    if not result:
        return jsonify({
            "status": "error", 
            "message": f"Exercise {exercise_id} not found."
        }), 404
    return jsonify({"status": "success", "exercises": result}), 200
