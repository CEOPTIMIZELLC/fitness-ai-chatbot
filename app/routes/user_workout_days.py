from logging_config import LogRoute

from flask import jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Phase_Library

from app.main_agent.user_workout_days import create_microcycle_scheduler_agent
from app.altering_agents.phase_components.actions import retrieve_parameters, retrieve_weekday_availability_information_from_availability
from app.solver_agents.phase_components import Main as phase_component_main

from app.utils.item_to_string import recursively_change_dict_timedeltas

bp = Blueprint('user_workout_days', __name__)

# ----------------------------------------- Workout Days -----------------------------------------

# Retrieve current user's phase components
@bp.route('/', methods=['GET'])
@login_required
def get_user_workout_days_list():
    state = {
        "user_id": current_user.id,
        "phase_component_is_requested": True,
        "phase_component_is_alter": False,
        "phase_component_is_read": True,
        "phase_component_read_plural": True,
        "phase_component_read_current": False,
        "phase_component_detail": "Perform phase component classification."
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
        "phase_component_is_requested": True,
        "phase_component_is_alter": False,
        "phase_component_is_read": True,
        "phase_component_read_plural": True,
        "phase_component_read_current": True,
        "phase_component_detail": "Perform phase component classification."
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
        "phase_component_is_requested": True,
        "phase_component_is_alter": False,
        "phase_component_is_read": True,
        "phase_component_read_plural": False,
        "phase_component_read_current": True,
        "phase_component_detail": "Perform phase component classification."
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
        "phase_component_is_requested": True,
        "phase_component_is_alter": True,
        "phase_component_is_read": True,
        "phase_component_read_plural": False,
        "phase_component_read_current": False,
        "phase_component_detail": "Perform phase component classification."
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
        "phase_component_is_requested": True,
        "phase_component_is_alter": True,
        "phase_component_is_read": True,
        "phase_component_read_plural": False,
        "phase_component_read_current": False,
        "phase_component_detail": "Perform phase component classification.",
        "phase_component_perform_with_parent_id": phase_id
    }
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    result = microcycle_scheduler_agent.invoke(state)
    return jsonify({"status": "success", "phase_components": result}), 200

# ---------- TEST ROUTES --------------

def perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose=False):
    parameters=retrieve_parameters(current_user.id, phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability)
    constraints={}

    result = phase_component_main(parameters, constraints)
    LogRoute.verbose(result["formatted"])
    return result

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

    weekday_availability_temp = [
        {"weekday_id": 0, "weekday_name": "Monday", "availability": 6 * 60 * 60},
        {"weekday_id": 1, "weekday_name": "Tuesday", "availability": 3 * 60 * 60},
        {"weekday_id": 2, "weekday_name": "Wednesday", "availability": 2 * 60 * 60},
        {"weekday_id": 3, "weekday_name": "Thursday", "availability": 35 * 60},
        {"weekday_id": 4, "weekday_name": "Friday", "availability": 0 * 60 * 60},
        {"weekday_id": 5, "weekday_name": "Saturday", "availability": 2 * 60 * 60},
        {"weekday_id": 6, "weekday_name": "Sunday", "availability": 0 * 60 * 60},
    ]

    microcycle_weekdays =  [0, 1, 2, 3, 4, 5, 6]

    weekday_availability, number_of_available_weekdays, total_availability = retrieve_weekday_availability_information_from_availability(weekday_availability_temp)

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