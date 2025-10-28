from logging_config import LogRoute

from flask import jsonify, abort
from flask_login import current_user, login_required

from app.models import User_Weekday_Availability

from app.main_sub_agents.user_workout_exercises import create_workout_agent as create_agent
from app.main_sub_agents.user_workout_completion import create_workout_completion_agent
from app.creation_agents.workout_schedule.actions import retrieve_parameters
from app.solver_agents.exercises import exercise_pc_main

from app.common_table_queries.phase_components import currently_active_item as current_workout_day

from .blueprint_factories import create_subagent_crud_blueprint

# ----------------------------------------- Workout Exercises -----------------------------------------

bp = create_subagent_crud_blueprint('user_workout_exercises', 'workout_schedule', '/user_workout_exercises', create_agent)

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
    return jsonify({"status": "success", "response": result}), 200

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
    workout_agent = create_agent()
    workout_completion_agent = create_workout_completion_agent()

    result["workout_exercises"] = workout_agent.invoke(state)
    result["exercises"] = workout_completion_agent.invoke(state)
    return jsonify({"status": "success", "response": result}), 200

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

# This is simply for the purposes of testing the phase component assignment stage.
@bp.route('/test_exercise_phase_components', methods=['POST', 'PATCH'])
@login_required
def exercise_phase_components_test():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        abort(404, description="No active workout day found.")

    availability = retrieve_availability_for_day(user_workout_day)
    if not availability:
        abort(404, description="No active weekday availability found.")

    parameters = retrieve_parameters(current_user.id, user_workout_day, availability)
    constraints={"vertical_loading": user_workout_day.loading_systems.id == 1}

    result = exercise_pc_main(parameters, constraints)
    LogRoute.verbose(result["formatted"])
    return jsonify({"status": "success", "response": result}), 200

# Assigns exercises to workouts.
@bp.route('/test_pre_processing', methods=['POST', 'PATCH'])
@login_required
def exercise_agent_preprocessing_test():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        abort(404, description="No active workout day found.")

    availability = retrieve_availability_for_day(user_workout_day)
    if not availability:
        abort(404, description="No active weekday availability found.")

    parameters = retrieve_parameters(current_user.id, user_workout_day, availability)
    return jsonify({"status": "success", "response": parameters}), 200


