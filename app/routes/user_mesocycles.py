from config import verbose
from flask import jsonify, Blueprint
from flask_login import current_user, login_required
from datetime import timedelta

from app import db
from app.models import (
    Goal_Library, 
    Goal_Phase_Requirements, 
    Phase_Library, 
    User_Mesocycles, 
    User_Macrocycles
)

from app.agents.phases import Main as phase_main
from app.utils.common_table_queries import current_macrocycle, current_mesocycle

bp = Blueprint('user_mesocycles', __name__)

# ----------------------------------------- User Mesocycles -----------------------------------------

def delete_old_user_phases(macrocycle_id):
    db.session.query(User_Mesocycles).filter_by(macrocycle_id=macrocycle_id).delete()
    if verbose:
        print("Successfully deleted")

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_phase_constraints_for_goal(goal_id):
    # Retrieve all possible phases that can be selected.
    possible_phases = (
        db.session.query(
            Phase_Library.id,
            Phase_Library.name,
            Phase_Library.phase_duration_minimum_in_weeks,
            Phase_Library.phase_duration_maximum_in_weeks,
            Goal_Phase_Requirements.required_phase,
            Goal_Phase_Requirements.is_goal_phase,
        )
        .join(Goal_Phase_Requirements, Goal_Phase_Requirements.phase_id == Phase_Library.id)
        .join(Goal_Library, Goal_Library.id == Goal_Phase_Requirements.goal_id)
        .filter(Goal_Library.id == goal_id)
        .order_by(Phase_Library.id.asc())
        .all()
    )

    return possible_phases

def construct_phases_list(possible_phases):
    # Convert the phases to a list form.
    possible_phases_list = [{
            "id": 0,
            "name": "Inactive",
            "element_minimum": 0,
            "element_maximum": 0,
            "required_phase": False,
            "is_goal_phase": False,
        }]

    for possible_phase in possible_phases:
        possible_phases_list.append({
            "id": possible_phase.id,
            "name": possible_phase.name.lower(),
            "element_minimum": possible_phase.phase_duration_minimum_in_weeks.days // 7,
            "element_maximum": possible_phase.phase_duration_maximum_in_weeks.days // 7,
            "required_phase": True if possible_phase.required_phase == "required" else False,
            #"required_phase": possible_phase.required_phase,
            "is_goal_phase": possible_phase.is_goal_phase,
        })
    return possible_phases_list

def perform_phase_selection(goal_id, macrocycle_allowed_weeks, verbose=False):
    parameters={
        "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
        "goal_type": goal_id}
    constraints={}

    # Retrieve all possible phases that can be selected and convert them into a list form.
    possible_phases = retrieve_phase_constraints_for_goal(int(goal_id))
    parameters["possible_phases"] = construct_phases_list(possible_phases)

    result = phase_main(parameters, constraints)

    if verbose:
        print(result["formatted"])
    return result

def mesocycle_phase_adding(goal_id=None):
    user_macro = current_macrocycle(current_user.id)
    if not user_macro:
        return jsonify({"status": "error", "message": "No active macrocycle found."}), 404
    
    if not goal_id:
        goal_id = user_macro.goal_id

    delete_old_user_phases(user_macro.id)
    result = perform_phase_selection(goal_id, 26, verbose)
    user_phases = agent_output_to_sqlalchemy_model(result["output"], user_macro.id, user_macro.start_date)
    db.session.add_all(user_phases)
    db.session.commit()
    return jsonify({"status": "success", "mesocycles": result}), 200

# Method to perform phase selection on a goal of a specified id.
def mesocycle_phases_by_id(goal_id, macrocycle_allowed_weeks):
    from app.utils.db_helpers import get_item_by_id
    goal = get_item_by_id(Goal_Library, goal_id)
    if not goal:
        return None

    return perform_phase_selection(goal_id, macrocycle_allowed_weeks, verbose)

def agent_output_to_sqlalchemy_model(phases_output, macrocycle_id, mesocycle_start_date):
    # Convert output to form that may be stored.
    user_phases = []
    order = 1
    for phase in phases_output:
        new_phase = User_Mesocycles(
            macrocycle_id = macrocycle_id,
            phase_id = phase["id"],
            order = order,
            start_date = mesocycle_start_date,
            end_date = mesocycle_start_date + timedelta(weeks=phase["duration"])
        )
        user_phases.append(new_phase)

        # Set startdate of next phase to be at the end of the current one.
        mesocycle_start_date +=timedelta(weeks=phase["duration"])
        order += 1
    return user_phases

# Retrieve current user's mesocycles
@bp.route('/', methods=['GET'])
@login_required
def get_user_mesocycles_list():
    user_mesocycles = User_Mesocycles.query.join(User_Macrocycles).filter_by(user_id=current_user.id).all()
    result = []
    for user_mesocycle in user_mesocycles:
        result.append(user_mesocycle.to_dict())
    return jsonify({"status": "success", "mesocycles": result}), 200

# Retrieve user's current macrocycles's mesocycles
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_mesocycles_list():
    result = []
    user_macrocycle = current_macrocycle(current_user.id)
    if not user_macrocycle:
        return jsonify({"status": "error", "message": "No active macrocycle found."}), 404
    user_mesocycles = user_macrocycle.mesocycles
    for user_mesocycle in user_mesocycles:
        result.append(user_mesocycle.to_dict())
    return jsonify({"status": "success", "mesocycles": result}), 200

# Retrieve user's current mesocycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_mesocycle():
    user_mesocycle = current_mesocycle(current_user.id)
    if not user_mesocycle:
        return jsonify({"status": "error", "message": "No active mesocycle found."}), 404
    return jsonify({"status": "success", "mesocycles": user_mesocycle.to_dict()}), 200

# Perform parameter programming for mesocycle labeling.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def mesocycle_phases():
    return mesocycle_phase_adding()

# Perform parameter programming for mesocycle labeling.
@bp.route('/<goal_id>', methods=['POST', 'PATCH'])
@login_required
def add_mesocycle_phases_by_id(goal_id):
    return mesocycle_phase_adding(goal_id)

# Test the phase selection by a goal id.
@bp.route('/test/<goal_id>', methods=['GET', 'POST'])
@login_required
def test_mesocycle_phases_by_id(goal_id):
    result = mesocycle_phases_by_id(goal_id, 26)
    if not result:
        return jsonify({"status": "error", "message": f"Goal {goal_id} not found."}), 404
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
        result = perform_phase_selection(goal.id, macrocycle_allowed_weeks, verbose)
        test_results.append({
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks, 
            "goal_id": goal.id,
            "result": result
        })
        if verbose:
            print(f"----------------------\n")

    return jsonify({"status": "success", "test_results": test_results}), 200