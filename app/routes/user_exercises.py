from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import User_Exercises, User_Equipment, Exercise_Library, Exercise_Supportive_Equipment, Exercise_Assistive_Equipment, Exercise_Weighted_Equipment, Exercise_Marking_Equipment, Exercise_Other_Equipment


from sqlalchemy.sql import func, distinct

from app.models import Equipment_Library

from app.utils.common_table_queries import user_available_exercises


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


# Retrieve available exercises for the current user
@bp.route('/available', methods=['GET'])
@login_required
def get_available_exercises():
    available_exercises = user_available_exercises(current_user.id)


    for exercise in available_exercises:

        supportive_equipment = [equipment.equipment.name for equipment in exercise.supportive_equipment]
        assistive_equipment = [equipment.equipment.name for equipment in exercise.assistive_equipment]
        weighted_equipment = [equipment.equipment.name for equipment in exercise.weighted_equipment]
        marking_equipment = [equipment.equipment.name for equipment in exercise.marking_equipment]
        other_equipment = [equipment.equipment.name for equipment in exercise.other_equipment]
        equipment = supportive_equipment + assistive_equipment + weighted_equipment + marking_equipment + other_equipment

        print(exercise.name, equipment)


    result = [exercise.to_dict() for exercise in available_exercises]
    return jsonify({"status": "success", "exercises": result}), 200