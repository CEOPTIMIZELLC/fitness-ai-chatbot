from logging_config import LogRoute

from flask import jsonify, Blueprint, abort
from flask_login import current_user, login_required

from app.models import User_Weekday_Availability

from app.solver_agents.exercises import exercise_pc_main

from app.utils.common_table_queries import current_workout_day

from app.main_agent.utils import retrieve_total_time_needed
from app.main_agent.utils import construct_user_workout_components_list, construct_available_exercises_list, construct_available_general_exercises_list
from app.main_agent.utils import verify_pc_information
from app.main_agent.user_workout_exercises import create_workout_agent
from app.main_agent.user_workout_completion import create_workout_completion_agent

bp = Blueprint('user_workout_exercises', __name__)

# ----------------------------------------- Workout Exercises -----------------------------------------

# Retrieve current user's workout exercises
@bp.route('/', methods=['GET'])
@login_required
def get_user_workout_exercises_list():
    state = {
        "user_id": current_user.id,
        "workout_schedule_is_requested": True,
        "workout_schedule_is_alter": False,
        "workout_schedule_is_read": True,
        "workout_schedule_read_plural": True,
        "workout_schedule_read_current": False,
        "workout_schedule_detail": "Perform workout scheduling."
    }
    workout_agent = create_workout_agent()

    result = workout_agent.invoke(state)
    return jsonify({"status": "success", "exercises": result}), 200

# Retrieve user's current microcycle's workout exercises
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_exercises_list():
    state = {
        "user_id": current_user.id,
        "workout_schedule_is_requested": True,
        "workout_schedule_is_alter": False,
        "workout_schedule_is_read": True,
        "workout_schedule_read_plural": True,
        "workout_schedule_read_current": True,
        "workout_schedule_detail": "Perform workout scheduling."
    }
    workout_agent = create_workout_agent()

    result = workout_agent.invoke(state)
    return jsonify({"status": "success", "exercises": result}), 200

# Assigns exercises to workouts.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def exercise_initializer():
    state = {
        "user_id": current_user.id,
        "workout_schedule_is_requested": True,
        "workout_schedule_is_alter": True,
        "workout_schedule_is_read": True,
        "workout_schedule_read_plural": False,
        "workout_schedule_read_current": False,
        "workout_schedule_detail": "Perform workout scheduling."
    }
    workout_agent = create_workout_agent()

    result = workout_agent.invoke(state)
    return jsonify({"status": "success", "exercises": result}), 200

# Update user exercises if workout is completed.
@bp.route('/workout_completed', methods=['POST', 'PATCH'])
@login_required
def complete_workout():
    state = {
        "user_id": current_user.id,
        "workout_completion_is_requested": True,
        "workout_completion_is_alter": True,
        "workout_completion_is_read": True,
        "workout_completion_read_plural": False,
        "workout_completion_read_current": False,
        "workout_completion_detail": "Perform workout scheduling."
    }
    workout_completion_agent = create_workout_completion_agent()

    result = workout_completion_agent.invoke(state)
    return jsonify({"status": "success", "exercises": result}), 200

# Combine Exercise Initializer and Complete Workout for testing.
@bp.route('/initialize_and_complete', methods=['POST', 'PATCH'])
@login_required
def initialize_and_complete():
    result = {}

    state = {
        "user_id": current_user.id,
        "workout_schedule_is_requested": True,
        "workout_schedule_is_alter": True,
        "workout_schedule_is_read": True,
        "workout_schedule_read_plural": False,
        "workout_schedule_read_current": False,
        "workout_schedule_detail": "Perform workout scheduling.",
        "workout_completion_is_requested": True,
        "workout_completion_is_alter": True,
        "workout_completion_is_read": True,
        "workout_completion_read_plural": False,
        "workout_completion_read_current": False,
        "workout_completion_detail": "Perform workout scheduling."
    }
    workout_agent = create_workout_agent()
    workout_completion_agent = create_workout_completion_agent()

    result["workout_exercises"] = workout_agent.invoke(state)
    result["exercises"] = workout_completion_agent.invoke(state)
    return jsonify({"status": "success", "output": result}), 200

# ---------- TEST ROUTES --------------

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
    # Retrieve parameters. Returned information includes the phase components, exercises, and exercises for phase components.
    pcs, exercises = verify_pc_information(parameters, pcs, exercises, parameters["availability"], "duration_min", "exercises_per_bodypart_workout_min", check_globally=True)
    
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
        abort(400, description="This phase component is inactive. No exercises for today.")

    # Retrieve availability for day.
    availability = retrieve_availability_for_day(user_workout_day)
    if not availability:
        abort(404, description="No active weekday availability found.")

    parameters["one_rep_max_improvement_percentage"] = 25
    parameters["availability"] = availability
    parameters["phase_components"] = construct_user_workout_components_list(user_workout_components)
    parameters["possible_exercises"] = construct_available_exercises_list(current_user.id)
    parameters["possible_general_exercises"] = construct_available_general_exercises_list(parameters["possible_exercises"])

    verify_and_update_pc_information(parameters, parameters["phase_components"][1:], parameters["possible_exercises"][1:])

    parameters["projected_duration"] = retrieve_projected_duration(parameters["phase_components"][1:], parameters["phase_components"][1:])
    return parameters

# This is simply for the purposes of testing the phase component assignment stage.
@bp.route('/test_exercise_phase_components', methods=['POST', 'PATCH'])
@login_required
def exercise_phase_components_test():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        abort(404, description="No active workout day found.")

    parameters = retrieve_pc_parameters(user_workout_day)
    constraints={"vertical_loading": user_workout_day.loading_systems.id == 1}

    result = exercise_pc_main(parameters, constraints)
    LogRoute.verbose(result["formatted"])
    return jsonify({"status": "success", "exercises": result}), 200

# Assigns exercises to workouts.
@bp.route('/test_pre_processing', methods=['POST', 'PATCH'])
@login_required
def exercise_agent_preprocessing_test():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        abort(404, description="No active workout day found.")
    parameters = retrieve_pc_parameters(user_workout_day)
    return jsonify({"status": "success", "parameters": parameters}), 200


