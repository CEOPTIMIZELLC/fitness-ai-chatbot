from flask import jsonify, Blueprint
from app.models import Goal_Library
from app.utils.db_helpers import get_all_items, get_item_by_id

bp = Blueprint('goals', __name__)

# ----------------------------------------- Goals -----------------------------------------

# Retrieve goals
@bp.route('/', methods=['GET'])
def get_goal_list():
    result = get_all_items(Goal_Library)
    return jsonify({"status": "success", "goals": result}), 200

# Show goals based on id.
@bp.route('/<goal_id>', methods=['GET'])
def read_goal(goal_id):
    result = get_item_by_id(Goal_Library, goal_id)
    if not result:
        return jsonify({
            "status": "error", 
            "message": f"Goal {goal_id} not found."
        }), 404
    return jsonify({"status": "success", "goals": result}), 200
