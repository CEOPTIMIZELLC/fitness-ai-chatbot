from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import User_Exercises, User_Equipment, Exercise_Library, Exercise_Supportive_Equipment, Exercise_Assistive_Equipment, Exercise_Weighted_Equipment, Exercise_Marking_Equipment, Exercise_Other_Equipment


from sqlalchemy.sql import func, distinct

from app.models import Equipment_Library

from app.utils.common_table_queries import user_available_exercises
from app.utils.common_table_queries import current_workout_day


bp = Blueprint('user_exercises', __name__)

# ----------------------------------------- User Exercises -----------------------------------------

# Retrieve current user's exercises.
@bp.route('/', methods=['GET'])
@login_required
def get_user_exercise_list():
    user_exercises = current_user.exercises
    result = []
    for user_exercise in user_exercises:
        result.append(user_exercise.to_dict())
    return jsonify({"status": "success", "user_exercises": result}), 200


# Retrieve current user's exercises.
@bp.route('/<exercise_id>', methods=['GET'])
@login_required
def read_user_exercise(exercise_id):
    user_exercise = db.session.get(User_Exercises, {"user_id": current_user.id, "exercise_id": exercise_id})
    if not user_exercise:
        return jsonify({"status": "error", "message": f"No active exercise of {exercise_id} found for current user."}), 404
    return jsonify({"status": "success", "user_exercises": user_exercise.to_dict()}), 200

# Retrieve current user's exercises for current workout.
@bp.route('/current', methods=['GET'])
@login_required
def get_user_current_exercise_list():
    result = []
    user_workout_day = current_workout_day(current_user.id)
    workout_exercises = user_workout_day.exercises

    for exercise in workout_exercises:
        user_exercise = db.session.get(User_Exercises, {"user_id": current_user.id, "exercise_id": exercise.exercise_id})
        result.append(user_exercise.to_dict())
    return jsonify({"status": "success", "user_exercises": result}), 200

# Retrieve available exercises for the current user
@bp.route('/available', methods=['GET'])
@login_required
def get_available_exercises():
    available_exercises = user_available_exercises(current_user.id)
    result = [exercise.to_dict() for exercise in available_exercises]
    return jsonify({"status": "success", "exercises": result}), 200