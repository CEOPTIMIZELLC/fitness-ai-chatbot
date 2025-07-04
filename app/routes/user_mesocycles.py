from config import verbose
from flask import jsonify, Blueprint, abort
from flask_login import login_required

from app import db
from app.models import Goal_Library, Goal_Phase_Requirements

from app.agents.phases import Main as phase_main
from app.main_agent.utils import construct_phases_list
from app.main_agent.user_mesocycles import MesocycleActions

bp = Blueprint('user_mesocycles', __name__)

# ----------------------------------------- User Mesocycles -----------------------------------------

def perform_phase_selection(goal_id, macrocycle_allowed_weeks):
    parameters={
        "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
        "goal_type": goal_id}
    constraints={}

    # Retrieve all possible phases that can be selected and convert them into a list form.
    parameters["possible_phases"] = construct_phases_list(int(goal_id))

    result = phase_main(parameters, constraints)

    if verbose:
        print(result["formatted"])
    return result

# Method to perform phase selection on a goal of a specified id.
def mesocycle_phases_by_id(goal_id, macrocycle_allowed_weeks):
    if not db.session.get(Goal_Library, goal_id):
        abort(404, description=f"Goal {goal_id} not found.")
    return perform_phase_selection(goal_id, macrocycle_allowed_weeks)

# Retrieve current user's mesocycles
@bp.route('/', methods=['GET'])
@login_required
def get_user_mesocycles_list():
    mesocycles = MesocycleActions.get_user_list()
    return jsonify({"status": "success", "mesocycles": mesocycles}), 200

# Retrieve user's current macrocycles's mesocycles
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_mesocycles_list():
    mesocycles = MesocycleActions.get_user_current_list()
    return jsonify({"status": "success", "mesocycles": mesocycles}), 200

# Retrieve user's current macrocycle's mesocycles
@bp.route('/current_formatted_list', methods=['GET'])
@login_required
def get_user_current_mesocycles_formatted_list():
    mesocycles = MesocycleActions.get_formatted_list()
    return jsonify({"status": "success", "mesocycles": mesocycles}), 200

# Retrieve user's current mesocycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_mesocycle():
    mesocycles = MesocycleActions.read_user_current_element()
    return jsonify({"status": "success", "mesocycles": mesocycles}), 200

# Perform parameter programming for mesocycle labeling.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def mesocycle_phases():
    result = MesocycleActions.scheduler()
    result["formatted_schedule"] = MesocycleActions.get_formatted_list()
    return jsonify({"status": "success", "mesocycles": result}), 200

# Perform parameter programming for mesocycle labeling.
@bp.route('/<goal_id>', methods=['POST', 'PATCH'])
@login_required
def add_mesocycle_phases_by_id(goal_id):
    result = MesocycleActions.scheduler(goal_id)
    result["formatted_schedule"] = MesocycleActions.get_formatted_list()
    return jsonify({"status": "success", "mesocycles": result}), 200

# ---------- TEST ROUTES --------------

# Test the phase selection by a goal id.
@bp.route('/test/<goal_id>', methods=['GET', 'POST'])
@login_required
def test_mesocycle_phases_by_id(goal_id):
    result = mesocycle_phases_by_id(goal_id, 26)
    return jsonify({"status": "success", "mesocycles": result}), 200

# Testing for the parameter programming for mesocycle labeling.
@bp.route('/test', methods=['GET', 'POST'])
def phase_classification_test():
    test_results = []
    parameters={}
    constraints={}

    parameters["macrocycle_allowed_weeks"] = 43

    # Test with default test values.
    result = phase_main(parameters, constraints)
    if verbose:
        print("TESTING")
        print(result["formatted"])
    test_results.append({
        "macrocycle_allowed_weeks": parameters["macrocycle_allowed_weeks"], 
        "goal_id": 0,
        "result": result
    })
    if verbose:
        print("----------------------")
    

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
        if verbose:
            print("----------------------")
            print(str(goal.id))
        result = perform_phase_selection(goal.id, macrocycle_allowed_weeks)
        test_results.append({
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks, 
            "goal_id": goal.id,
            "result": result
        })
        if verbose:
            print(f"----------------------\n")

    return jsonify({"status": "success", "test_results": test_results}), 200