from logging_config import LogRoute
from flask import jsonify, Blueprint
from flask_login import login_required, current_user

from app import db
from app.models import Goal_Library, Goal_Phase_Requirements

from app.solver_agents.phases import Main as phase_main
from app.main_agent.utils import construct_phases_list
from app.main_agent.user_mesocycles import create_mesocycle_agent

bp = Blueprint('user_mesocycles', __name__)

# ----------------------------------------- User Mesocycles -----------------------------------------

# Retrieve current user's mesocycles
@bp.route('/', methods=['GET'])
@login_required
def get_user_mesocycles_list():
    state = {
        "user_id": current_user.id,
        "mesocycle_is_requested": True,
        "mesocycle_is_altered": False,
        "mesocycle_is_read": True,
        "mesocycle_read_plural": True,
        "mesocycle_read_current": False,
        "mesocycle_detail": "Retrieve mesocycle scheduling."
    }
    mesocycle_agent = create_mesocycle_agent()

    result = mesocycle_agent.invoke(state)
    return jsonify({"status": "success", "mesocycles": result}), 200

# Retrieve user's current macrocycle's mesocycles
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_mesocycles_list():
    state = {
        "user_id": current_user.id,
        "mesocycle_is_requested": True,
        "mesocycle_is_altered": False,
        "mesocycle_is_read": True,
        "mesocycle_read_plural": True,
        "mesocycle_read_current": True,
        "mesocycle_detail": "Retrieve mesocycle scheduling."
    }
    mesocycle_agent = create_mesocycle_agent()

    result = mesocycle_agent.invoke(state)
    return jsonify({"status": "success", "mesocycles": result}), 200

# Retrieve user's current mesocycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_mesocycle():
    state = {
        "user_id": current_user.id,
        "mesocycle_is_requested": True,
        "mesocycle_is_altered": False,
        "mesocycle_is_read": True,
        "mesocycle_read_plural": False,
        "mesocycle_read_current": True,
        "mesocycle_detail": "Retrieve mesocycle scheduling."
    }
    mesocycle_agent = create_mesocycle_agent()

    result = mesocycle_agent.invoke(state)
    return jsonify({"status": "success", "mesocycles": result}), 200

# Perform parameter programming for mesocycle labeling.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def mesocycle_phases():
    state = {
        "user_id": current_user.id,
        "mesocycle_is_requested": True,
        "mesocycle_is_altered": True,
        "mesocycle_is_read": True,
        "mesocycle_read_plural": False,
        "mesocycle_read_current": False,
        "mesocycle_detail": "Perform mesocycle scheduling."
    }
    mesocycle_agent = create_mesocycle_agent()

    result = mesocycle_agent.invoke(state)
    return jsonify({"status": "success", "mesocycles": result}), 200

# Perform parameter programming for mesocycle labeling.
@bp.route('/<goal_id>', methods=['POST', 'PATCH'])
@login_required
def add_mesocycle_phases_by_id(goal_id):
    state = {
        "user_id": current_user.id,
        "mesocycle_is_requested": True,
        "mesocycle_is_altered": True,
        "mesocycle_is_read": True,
        "mesocycle_read_plural": False,
        "mesocycle_read_current": False,
        "mesocycle_detail": "Perform mesocycle scheduling.",
        "mesocycle_perform_with_parent_id": goal_id
    }
    mesocycle_agent = create_mesocycle_agent()

    result = mesocycle_agent.invoke(state)
    return jsonify({"status": "success", "mesocycles": result}), 200

# ---------- TEST ROUTES --------------

def perform_phase_selection(goal_id, macrocycle_allowed_weeks):
    parameters={
        "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
        "goal_type": goal_id}
    constraints={}

    # Retrieve all possible phases that can be selected and convert them into a list form.
    parameters["possible_phases"] = construct_phases_list(int(goal_id))

    result = phase_main(parameters, constraints)

    LogRoute.verbose(result["formatted"])
    return result

# Testing for the parameter programming for mesocycle labeling.
@bp.route('/test', methods=['GET', 'POST'])
def phase_classification_test():
    test_results = []
    parameters={}
    constraints={}

    parameters["macrocycle_allowed_weeks"] = 43

    # Test with default test values.
    result = phase_main(parameters, constraints)
    LogRoute.verbose("TESTING")
    LogRoute.verbose(result["formatted"])
    test_results.append({
        "macrocycle_allowed_weeks": parameters["macrocycle_allowed_weeks"], 
        "goal_id": 0,
        "result": result
    })
    LogRoute.verbose("----------------------")
    

    # Retrieve all possible goals.
    goals = (
        db.session.query(Goal_Library.id)
        .join(Goal_Phase_Requirements, Goal_Library.id == Goal_Phase_Requirements.goal_id)  # Adjust column names as necessary
        .group_by(Goal_Library.id)
        .order_by(Goal_Library.id.asc())
        .all()
    )

    macrocycle_allowed_weeks = 43

    # Test for all goals that exist.
    for goal in goals:
        LogRoute.verbose("----------------------")
        LogRoute.verbose(str(goal.id))
        result = perform_phase_selection(goal.id, macrocycle_allowed_weeks)
        test_results.append({
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks, 
            "goal_id": goal.id,
            "result": result
        })
        LogRoute.verbose(f"----------------------\n")

    return jsonify({"status": "success", "test_results": test_results}), 200