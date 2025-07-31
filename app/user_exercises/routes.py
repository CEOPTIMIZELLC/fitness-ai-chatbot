from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_required

from app import db
from app.models import User_Exercises

from app.user_exercises.retrieve_possible import user_possible_exercises, user_possible_exercises_with_user_exercise_info, user_available_exercises
from app.user_workout_days.retrieve_current import current_workout_day

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
        abort(404, description=f"No active exercise of {exercise_id} found for current user.")
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
    result = [exercise.to_dict() 
              for exercise in available_exercises]
    return jsonify({"status": "success", "exercises": result}), 200

# Retrieve current user's exercises.
@bp.route('/possible', methods=['GET'])
@login_required
def get_user_possible_exercise_list():
    available_exercises = user_possible_exercises(current_user.id)
    result = [exercise.to_dict() 
              for exercise in available_exercises]
    return jsonify({"status": "success", "exercises": result}), 200

def exercise_dict(exercise, user_exercise):
    """Format the exercise data."""
    return {
        "id": exercise.id,
        "name": exercise.name.lower(),
        "base_strain": exercise.base_strain,
        "technical_difficulty": exercise.technical_difficulty,
        # "component_ids": [component_phase.component_id for component_phase in exercise.component_phases],
        # "subcomponent_ids": [component_phase.subcomponent_id for component_phase in exercise.component_phases],
        # "components": [component_phase.components.name for component_phase in exercise.component_phases],
        # "subcomponents": [component_phase.subcomponents.name for component_phase in exercise.component_phases],
        "phase_components": [(component_phase.components.name + "-" + component_phase.subcomponents.name) for component_phase in exercise.component_phases],
        # "phase_component_name": [component_phase.name for component_phase in exercise.component_phases],
        # "body_region_ids": exercise.all_body_region_ids,
        # "bodypart_ids": exercise.all_bodypart_ids,
        # "muscle_group_ids": exercise.all_muscle_group_ids,
        # "muscle_ids": exercise.all_muscle_ids,
        # "supportive_equipment_ids": exercise.all_supportive_equipment,
        # "assistive_equipment_ids": exercise.all_assistive_equipment,
        # "weighted_equipment_ids": exercise.all_weighted_equipment,
        # "is_weighted": exercise.is_weighted,
        # "marking_equipment_ids": exercise.all_marking_equipment,
        # "other_equipment_ids": exercise.all_other_equipment,
        "one_rep_max": float(user_exercise.one_rep_max),
        "one_rep_load": float(user_exercise.one_rep_load),
        "volume": float(user_exercise.volume),
        "density": float(user_exercise.density),
        "intensity": user_exercise.intensity,
        "performance": float(user_exercise.performance),
    }


# Retrieve current user's exercises with information.
@bp.route('/possible_with_info', methods=['GET'])
@login_required
def get_user_possible_exercise_list_with_info():
    user_exercises = user_possible_exercises_with_user_exercise_info(current_user.id)
    result = [exercise_dict(exercise, user_exercise) 
              for exercise, user_exercise in user_exercises]
    return jsonify({"status": "success", "user_exercises": result}), 200
