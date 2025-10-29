from logging_config import LogRoute

from flask import jsonify
from flask_login import current_user, login_required

from app import db
from app.models import Phase_Library

from app.main_sub_agents.user_workout_days import create_microcycle_scheduler_agent as create_agent
from app.creation_agents.phase_components.actions import retrieve_parameters, retrieve_weekday_availability_information_from_availability
from app.solver_agents.phase_components import Main as phase_component_main

from app.database_to_frontend.user_workout_days import ItemRetriever, CurrentRetriever

from .blueprint_factories.subagent_items import *

# ----------------------------------------- Workout Days -----------------------------------------

item_name = "user_workout_days"
focus_name = "phase_component"

bp = create_subagent_crud_blueprint(
    name = item_name, 
    url_prefix = "/" + item_name, 
    item_class = ItemRetriever
)
bp = add_current_retrievers_to_subagent_crud_blueprint(
    bp = bp, 
    item_class = CurrentRetriever
)
bp = add_test_retrievers_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = focus_name, 
    agent_creation_caller = create_agent
)
bp = add_initializer_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = focus_name, 
    agent_creation_caller = create_agent
)

# ---------- TEST ROUTES --------------

def perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose=False):
    parameters=retrieve_parameters(current_user.id, phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability)
    constraints={}

    result = phase_component_main(parameters, constraints)
    LogRoute.verbose(result["formatted"])
    return result

# Testing for the parameter programming for phase component assignment.
@bp.route('/test', methods=['GET', 'POST'])
@login_required
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

    return jsonify({"status": "success", "response": test_results}), 200