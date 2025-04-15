from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import User_Exercises

bp = Blueprint('user_exercises', __name__)

# ----------------------------------------- User Exercises -----------------------------------------

# Retrieve current user's goals
@bp.route('/', methods=['GET'])
@login_required
def get_user_exercise_list():
    user_exercises = current_user.exercises
    result = []
    for user_exercise in user_exercises:
        result.append(user_exercise.to_dict())
    return jsonify({"status": "success", "user_exercises": result}), 200


# Retrieve current user's goals
@bp.route('/<exercise_id>', methods=['GET'])
@login_required
def read_user_exercise(exercise_id):
    user_exercise = db.session.get(User_Exercises, {"user_id": current_user.id, "exercise_id": exercise_id})
    if not user_exercise:
        return jsonify({"status": "error", "message": f"No active exercise of {exercise_id} found for current user."}), 404
    return jsonify({"status": "success", "user_exercises": user_exercise.to_dict()}), 200