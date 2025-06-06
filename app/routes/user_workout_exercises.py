from config import verbose
import random
import math

from flask import jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import (
    User_Exercises, 
    User_Weekday_Availability, 
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days, 
    User_Workout_Exercises
)

from app.agents.exercises import exercises_main, exercise_pc_main

from app.utils.common_table_queries import current_workout_day
from app.utils.print_long_output import print_long_output

from app.routes.utils import retrieve_total_time_needed
from app.routes.utils import construct_user_workout_components_list, construct_available_exercises_list

from app.routes.utils import verify_pc_information

bp = Blueprint('user_workout_exercises', __name__)

# ----------------------------------------- Workout Exercises -----------------------------------------


def delete_old_user_workout_exercises(workout_day_id):
    db.session.query(User_Workout_Exercises).filter_by(workout_day_id=workout_day_id).delete()
    if verbose:
        print("Successfully deleted")
    return None

def retrieve_availability_for_day(user_workout_day):
    # Retrieve availability for day.
    availability = (
        User_Weekday_Availability.query
        .filter_by(user_id=current_user.id, weekday_id=user_workout_day.weekday_id)
        .first())
    if availability: 
        return int(availability.availability.total_seconds())
    return None

# Verifies and updates the phase component information.
# Updates the maximum allowed exercises to be the number of allowed exercises for a phase component if the number available is lower than the maximum.
def verify_and_update_pc_information(parameters, pcs, exercises):
    # Retrieve parameters. If a tuple is returned, that means they are the phase components, exercises, and exercises for phase components.
    verification_message = verify_pc_information(parameters, pcs, exercises, parameters["availability"], "duration_min", "exercises_per_bodypart_workout_min", check_globally=True)
    if isinstance(verification_message, tuple):
        pcs, exercises = verification_message
    else:
        return verification_message
    
    pcs_new = [pc for pc in pcs if pc.get("allowed_exercises")]

    # Replace the ends of both lists with the corrected versions. 
    parameters["phase_components"][1:] = pcs_new
    parameters["possible_exercises"][1:] = exercises
    return None

# Retrieves the total projected duration for the workout. 
# Updates the projected duration to be the maximum allowed time given the exercises available if this would be lower.
def retrieve_projected_duration(user_workout_components, pcs):
    # Get the total desired duration.
    projected_duration = 0
    for user_workout_component in user_workout_components:
        projected_duration += user_workout_component["duration"]

    # If the maximum possible duration is larger than the projected duration, lower the projected duration to be this maximum.
    max_time_possible = retrieve_total_time_needed(pcs, "duration_max", "exercises_per_bodypart_workout_max")
    return min(max_time_possible, projected_duration)

# Retrieves the parameters used by the solver.
# Information included:
#   The length allowed for the workout.
#   The projected duration of the workout.
#   The phase component information relevant for the workout.
#   The exercises that can be assigned in the workout.
def retrieve_pc_parameters(user_workout_day):
    parameters = {"valid": True, "status": None}

    # Retrieve user components
    user_workout_components = user_workout_day.workout_components
    if not user_workout_components:
        return jsonify({"status": "error", "exercises": "This phase component is inactive. No exercises for today."}), 400

    # Retrieve availability for day.
    availability = retrieve_availability_for_day(user_workout_day)
    if not availability:
        return jsonify({"status": "error", "message": "No active weekday availability found."}), 404

    parameters["one_rep_max_improvement_percentage"] = 25
    parameters["availability"] = availability
    parameters["phase_components"] = construct_user_workout_components_list(user_workout_components)
    parameters["possible_exercises"] = construct_available_exercises_list(current_user.id)

    pc_verification_message = verify_and_update_pc_information(parameters, parameters["phase_components"][1:], parameters["possible_exercises"][1:])
    if pc_verification_message:
        return jsonify({"status": "error", "message": pc_verification_message}), 400

    parameters["projected_duration"] = retrieve_projected_duration(parameters["phase_components"][1:], parameters["phase_components"][1:])
    return parameters

def agent_output_to_sqlalchemy_model(exercises_output, workout_day_id):
    new_exercises = []
    for i, exercise in enumerate(exercises_output, start=1):
        # Create a new exercise entry.
        new_exercise = User_Workout_Exercises(
            workout_day_id = workout_day_id,
            phase_component_id = exercise["phase_component_id"],
            exercise_id = exercise["exercise_id"],
            #bodypart_id = exercise["bodypart_id"],
            order = i,
            reps = exercise["reps_var"],
            sets = exercise["sets_var"],
            intensity = exercise["intensity_var"],
            rest = exercise["rest_var"],
            weight = exercise["training_weight"],
        )

        new_exercises.append(new_exercise)
    return new_exercises

# Retrieve current user's workout exercises
@bp.route('/', methods=['GET'])
@login_required
def get_user_workout_exercises_list():
    user_workout_exercises = (
        User_Workout_Exercises.query
        .join(User_Workout_Days)
        .join(User_Microcycles)
        .join(User_Mesocycles)
        .join(User_Macrocycles)
        .filter_by(user_id=current_user.id)
        .all())

    result = []
    for user_workout_exercise in user_workout_exercises:
        result.append(user_workout_exercise.to_dict())
    return jsonify({"status": "success", "exercises": result}), 200

# Retrieve user's current microcycle's workout exercises
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_exercises_list():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active workout day found."}), 404

    user_workout_exercises = user_workout_day.exercises
    result = [user_workout_exercise.to_dict() 
              for user_workout_exercise in user_workout_exercises]
    return jsonify({"status": "success", "exercises": result}), 200

# Assigns exercises to workouts.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def exercise_initializer():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active workout day found."}), 404

    delete_old_user_workout_exercises(user_workout_day.id)

    # Retrieve parameters. If a tuple error message is returned, return 
    parameters = retrieve_pc_parameters(user_workout_day)
    if isinstance(parameters, tuple):
        return parameters
    constraints={"vertical_loading": user_workout_day.loading_systems.id == 1}

    result = exercises_main(parameters, constraints)
    if verbose:
        print_long_output(result["formatted"])

    user_workout_exercises = agent_output_to_sqlalchemy_model(result["output"], user_workout_day.id)

    db.session.add_all(user_workout_exercises)
    db.session.commit()
    return jsonify({"status": "success", "exercises": result}), 200

# Update user exercises if workout is completed.
@bp.route('/workout_completed', methods=['POST', 'PATCH'])
@login_required
def complete_workout():
    result = []
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active workout day found."}), 404
    workout_exercises = user_workout_day.exercises

    for exercise in workout_exercises:
        user_exercise = db.session.get(User_Exercises, {"user_id": current_user.id, "exercise_id": exercise.exercise_id})

        new_weight = exercise.weight or 0

        new_one_rep_max = round((new_weight * (30 + exercise.reps)) / 30, 2)

        # Only replace if the new one rep max is larger.
        user_exercise.one_rep_max = max(user_exercise.one_rep_max_decayed, new_one_rep_max)
        user_exercise.one_rep_load = new_one_rep_max
        user_exercise.volume = exercise.volume
        user_exercise.density = exercise.density
        user_exercise.intensity = exercise.intensity
        user_exercise.duration = exercise.duration
        user_exercise.working_duration = exercise.working_duration
        user_exercise.last_performed = exercise.workout_days.date

        # Only replace if the new performance is larger.
        user_exercise.performance = max(user_exercise.performance_decayed, exercise.performance)

        db.session.commit()

        result.append(user_exercise.to_dict())

    return jsonify({"status": "success", "user_exercises": result}), 200

# Combine Exercise Initializer and Complete Workout for testing.
@bp.route('/initialize_and_complete', methods=['POST', 'PATCH'])
@login_required
def initialize_and_complete():
    result = {}
    exercise_initializer_result = exercise_initializer()
    # Return error if nothing is found.
    if exercise_initializer_result[1] == 404:
        return exercise_initializer_result
    complete_workout_result = complete_workout()

    # Return error if nothing is found.
    if complete_workout_result[1] == 404:
        return complete_workout_result
    result["user_workout_exercises"] = exercise_initializer_result[0].get_json()["exercises"]["output"]
    result["user_exercises"] = complete_workout_result[0].get_json()["user_exercises"]
    return jsonify({"status": "success", "output": result}), 200

# This is simply for the purposes of testing the phase component assignment stage.
@bp.route('/test_exercise_phase_components', methods=['POST', 'PATCH'])
@login_required
def exercise_phase_components_test():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active workout day found."}), 404

    # Retrieve parameters. If a tuple error message is returned, return 
    parameters = retrieve_pc_parameters(user_workout_day)
    if isinstance(parameters, tuple):
        return parameters
    constraints={"vertical_loading": user_workout_day.loading_systems.id == 1}

    result = exercise_pc_main(parameters, constraints)
    if verbose:
        print_long_output(result["formatted"])
    return jsonify({"status": "success", "exercises": result}), 200
