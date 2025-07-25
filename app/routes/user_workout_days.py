from logging_config import LogRoute
from flask import jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Phase_Library
from app.agents.phase_components import Main as phase_component_main
from app.main_agent.utils import construct_available_exercises_list, construct_phase_component_list, construct_available_general_exercises_list
from app.main_agent.utils import verify_pc_information
from app.main_agent.user_workout_days import create_microcycle_scheduler_agent

from .utils import recursively_change_dict_timedeltas

bp = Blueprint('user_workout_days', __name__)

# ----------------------------------------- Workout Days -----------------------------------------

# Retrieve current user's phase components
@bp.route('/', methods=['GET'])
@login_required
def get_user_workout_days_list():
    state = {
        "user_id": current_user.id,
        "phase_component_impacted": True,
        "phase_component_is_altered": False,
        "phase_component_read_plural": True,
        "phase_component_read_current": False,
        "phase_component_message": "Perform phase component classification."
    }
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    result = microcycle_scheduler_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"status": "success", "phase_components": result}), 200

# Retrieve user's current microcycle's phase components
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_workout_days_list():
    state = {
        "user_id": current_user.id,
        "phase_component_impacted": True,
        "phase_component_is_altered": False,
        "phase_component_read_plural": True,
        "phase_component_read_current": True,
        "phase_component_message": "Perform phase component classification."
    }
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    result = microcycle_scheduler_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"status": "success", "phase_components": result}), 200

# Retrieve user's current phase component
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_workout_day():
    state = {
        "user_id": current_user.id,
        "phase_component_impacted": True,
        "phase_component_is_altered": False,
        "phase_component_read_plural": False,
        "phase_component_read_current": True,
        "phase_component_message": "Perform phase component classification."
    }
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    result = microcycle_scheduler_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"status": "success", "phase_components": result}), 200

# Assigns phase components to days along with projected length.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def workout_day_initializer():
    state = {
        "user_id": current_user.id,
        "phase_component_impacted": True,
        "phase_component_is_altered": True,
        "phase_component_read_plural": False,
        "phase_component_read_current": False,
        "phase_component_message": "Perform phase component classification."
    }
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    result = microcycle_scheduler_agent.invoke(state)
    return jsonify({"status": "success", "phase_components": result}), 200

# Assigns phase components to days along with projected length.
@bp.route('/<phase_id>', methods=['POST', 'PATCH'])
@login_required
def workout_day_initializer_by_id(phase_id):
    state = {
        "user_id": current_user.id,
        "phase_component_impacted": True,
        "phase_component_is_altered": True,
        "phase_component_read_plural": False,
        "phase_component_read_current": False,
        "phase_component_message": "Perform phase component classification.",
        "phase_component_perform_with_parent_id": phase_id
    }
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    result = microcycle_scheduler_agent.invoke(state)
    return jsonify({"status": "success", "phase_components": result}), 200

# ---------- TEST ROUTES --------------

# Verifies and updates the phase component information.
# Updates the lower bound for duration if the user's current performance for all exercises in a phase component requires a higher minimum.
# Checks if the minimum amount of exercises allowed could fit into the workout with the current duration. 
# Checks if there are enough exercises to meet the minimum amount of exercises for a phase component. 
# Updates the maximum allowed exercises to be the number of allowed exercises for a phase component if the number available is lower than the maximum.
def verify_and_update_pc_information(parameters, pcs, exercises, total_availability, number_of_available_weekdays):
    pc_info = verify_pc_information(parameters, pcs, exercises, total_availability, "duration_min_for_day", "frequency_per_microcycle_min", check_globally=False, default_count_if_none=number_of_available_weekdays)
    pcs = pc_info[0]
    parameters["phase_components"] = pcs
    return None

# Retrieves the parameters used by the solver.
def retrieve_pc_parameters(phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability):
    parameters = {"valid": True, "status": None}

    parameters["microcycle_weekdays"] = microcycle_weekdays
    parameters["weekday_availability"] = weekday_availability
    parameters["phase_components"] = construct_phase_component_list(phase_id)
    parameters["possible_exercises"] = construct_available_exercises_list(current_user.id)
    parameters["possible_general_exercises"] = construct_available_general_exercises_list(parameters["possible_exercises"])

    verify_and_update_pc_information(parameters, parameters["phase_components"], parameters["possible_exercises"][1:], total_availability, number_of_available_weekdays)

    return parameters

def perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose=False):
    parameters=retrieve_pc_parameters(phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability)
    constraints={}

    result = phase_component_main(parameters, constraints)
    LogRoute.verbose(result["formatted"])
    return result

def retrieve_availability_for_test():
    weekday_availability_temp = [
        {"id": 0, "name": "Monday", "availability": 6 * 60 * 60},
        {"id": 1, "name": "Tuesday", "availability": 3 * 60 * 60},
        {"id": 2, "name": "Wednesday", "availability": 2 * 60 * 60},
        {"id": 3, "name": "Thursday", "availability": 35 * 60},
        {"id": 4, "name": "Friday", "availability": 0 * 60 * 60},
        {"id": 5, "name": "Saturday", "availability": 2 * 60 * 60},
        {"id": 6, "name": "Sunday", "availability": 0 * 60 * 60},
    ]
    microcycle_weekdays =  [0, 1, 2, 3, 4, 5, 6]
    weekday_availability = []

    number_of_available_weekdays = 0
    total_availability = 0
    for day in microcycle_weekdays:
        availability = weekday_availability_temp[day]["availability"]
        weekday_availability.append({
            "id": weekday_availability_temp[day]["id"], 
            "name": weekday_availability_temp[day]["name"].title(), 
            "availability": availability
        })
        total_availability += availability
        if availability > 0:
            number_of_available_weekdays += 1
    return microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability

# Testing for the parameter programming for phase component assignment.
@bp.route('/test', methods=['GET', 'POST'])
def phase_component_classification_test():
    test_results = []

    # Retrieve all possible phases.
    phases = (
        db.session.query(Phase_Library.id)
        .group_by(Phase_Library.id)
        .order_by(Phase_Library.id.asc())
        .all()
    )

    microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability = retrieve_availability_for_test()

    for phase in phases:
        result = perform_workout_day_selection(phase.id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays)
        LogRoute.verbose(str(phase.id))
        LogRoute.verbose(result["formatted"])
        test_results.append({
            # "phase_components": parameters["phase_components"], 
            "phase_id": phase.id,
            "result": result
        })
        LogRoute.verbose("----------------------")

    return jsonify({"status": "success", "test_results": test_results}), 200