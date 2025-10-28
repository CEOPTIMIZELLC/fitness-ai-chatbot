from logging_config import LogRoute
from flask import jsonify, Blueprint
from flask_login import login_required

from app import db
from app.models import Goal_Library, Goal_Phase_Requirements

from app.solver_agents.phases import Main as phase_main
from app.construct_lists_from_sql.phases import Main as construct_phases_list
from app.main_sub_agents.user_mesocycles import create_mesocycle_agent as create_agent

bp = Blueprint('user_mesocycles', __name__)

from .blueprint_factories import get_user_list, get_user_current_list, read_user_current, item_initializer, item_initializer_with_parent_id

# ----------------------------------------- User Mesocycles -----------------------------------------

# Retrieve current user's mesocycles
@bp.route('/', methods=['GET'])
@login_required
def get_user_mesocycles_list():
    return get_user_list(focus_name="mesocycle", agent_creation_caller=create_agent)

# Retrieve user's current macrocycle's mesocycles
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_mesocycles_list():
    return get_user_current_list(focus_name="mesocycle", agent_creation_caller=create_agent)

# Retrieve user's current mesocycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_mesocycle():
    return read_user_current(focus_name="mesocycle", agent_creation_caller=create_agent)

# Perform parameter programming for mesocycle labeling.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def mesocycle_phases():
    return item_initializer(focus_name="mesocycle", agent_creation_caller=create_agent)

# Perform parameter programming for mesocycle labeling.
@bp.route('/<goal_id>', methods=['POST', 'PATCH'])
@login_required
def add_mesocycle_phases_by_id(goal_id):
    return item_initializer_with_parent_id(focus_name="mesocycle", agent_creation_caller=create_agent, parent_id=goal_id)

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

    return jsonify({"status": "success", "response": test_results}), 200