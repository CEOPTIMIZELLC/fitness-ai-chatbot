from config import verbose, verbose_formatted_schedule
from flask import jsonify, Blueprint, abort
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

from app.routes.utils import construct_phases_list
from app.routes.utils import print_mesocycles_schedule
from app.routes.utils import retrieve_output_from_endpoint

bp = Blueprint('user_mesocycles', __name__)

# ----------------------------------------- User Mesocycles -----------------------------------------

def delete_old_user_phases(macrocycle_id):
    db.session.query(User_Mesocycles).filter_by(macrocycle_id=macrocycle_id).delete()
    if verbose:
        print("Successfully deleted")

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

def mesocycle_phase_adding(goal_id=None):
    user_macro = current_macrocycle(current_user.id)
    if not user_macro:
        abort(404, description="No active macrocycle found.")
    
    if not goal_id:
        goal_id = user_macro.goal_id

    delete_old_user_phases(user_macro.id)
    result = perform_phase_selection(goal_id, 26)
    user_phases = agent_output_to_sqlalchemy_model(result["output"], user_macro.id, user_macro.start_date)
    db.session.add_all(user_phases)
    db.session.commit()

    result_temp = get_user_current_mesocycles_formatted_list()
    result["formatted_schedule"], _ = retrieve_output_from_endpoint(result_temp, "mesocycles")

    return jsonify({"status": "success", "mesocycles": result}), 200

# Method to perform phase selection on a goal of a specified id.
def mesocycle_phases_by_id(goal_id, macrocycle_allowed_weeks):
    if not db.session.get(Goal_Library, goal_id):
        abort(404, description=f"Goal {goal_id} not found.")
    return perform_phase_selection(goal_id, macrocycle_allowed_weeks)

def agent_output_to_sqlalchemy_model(phases_output, macrocycle_id, mesocycle_start_date):
    # Convert output to form that may be stored.
    user_phases = []
    order = 1
    for phase in phases_output:
        new_phase = User_Mesocycles(
            macrocycle_id = macrocycle_id,
            phase_id = phase["id"],
            is_goal_phase = phase["is_goal_phase"],
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
        abort(404, description="No active macrocycle found.")
    user_mesocycles = user_macrocycle.mesocycles
    for user_mesocycle in user_mesocycles:
        result.append(user_mesocycle.to_dict())
    return jsonify({"status": "success", "mesocycles": result}), 200

# Retrieve user's current macrocycle's mesocycles
@bp.route('/current_formatted_list', methods=['GET'])
@login_required
def get_user_current_mesocycles_formatted_list():
    user_macrocycle = current_macrocycle(current_user.id)
    if not user_macrocycle:
        abort(404, description="No active macrocycle found.")

    user_mesocycles = user_macrocycle.mesocycles
    if not user_mesocycles:
        abort(404, description="No mesocycles found for the macrocycle.")

    user_mesocycles_dict = [user_mesocycle.to_dict() for user_mesocycle in user_mesocycles]

    formatted_schedule = print_mesocycles_schedule(user_mesocycles_dict)
    if verbose_formatted_schedule:
        print(formatted_schedule)
    return jsonify({"status": "success", "mesocycles": formatted_schedule}), 200

# Retrieve user's current mesocycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_mesocycle():
    user_mesocycle = current_mesocycle(current_user.id)
    if not user_mesocycle:
        abort(404, description="No active mesocycle found.")
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