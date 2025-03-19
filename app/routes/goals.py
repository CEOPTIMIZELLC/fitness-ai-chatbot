from flask import request, jsonify, Blueprint

from app.models import Goal_Library

bp = Blueprint('goals', __name__)

# ----------------------------------------- Goals -----------------------------------------

# Retrieve goals
@bp.route('/', methods=['GET'])
def get_goal_list():
    goals = Goal_Library.query.all()
    result = []
    for goal in goals:
        result.append(goal.to_dict())
    return jsonify({"status": "success", "goals": result}), 200

# Show goals based on id.
@bp.route('/<goal_id>', methods=['GET'])
def read_goal(goal_id):
    goal = Goal_Library.query.filter_by(id=goal_id).first()
    if not goal:
        return jsonify({"status": "error", "message": "Goal " + goal_id + " not found."}), 404
    return jsonify(goal.to_dict()), 200
