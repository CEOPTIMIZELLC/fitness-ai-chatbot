from flask import request, jsonify, Blueprint, abort
from flask_login import login_required, current_user

from app import db
from app.models import Goal_Library

from app.agents.goals import create_goal_classification_graph
from app.main_agent.user_macrocycles import create_goal_agent, MacrocycleActions

bp = Blueprint('user_macrocycles', __name__)

# ----------------------------------------- User Macrocycles -----------------------------------------
# Retrieve possible goal types.
def retrieve_goal_types():
    goals = db.session.query(Goal_Library.id, Goal_Library.name).all()

    return [
        {
            "id": goal.id, 
            "name": goal.name.lower()
        } 
        for goal in goals
    ]

def goal_classification_test_run(goal_app, goal_types, user_goal):
    result_temp = goal_app.invoke(
        {
            "new_goal": user_goal, 
            "goal_types": goal_types, 
            "attempts": 0
        })
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")
    return {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}

# Retrieve current user's macrocycles
@bp.route('/', methods=['GET'])
@login_required
def get_user_macrocycle_list():
    macrocycles = MacrocycleActions.get_user_list()
    return jsonify({"status": "success", "macrocycles": macrocycles}), 200


# Retrieve current user's macrocycles
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_macrocycle():
    macrocycles = MacrocycleActions.read_user_current_element()
    return jsonify({"status": "success", "macrocycles": macrocycles}), 200

# Change the current user's macrocycle.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def change_macrocycle():
    # Input is a json.
    data = request.get_json()
    if not data:
        abort(404, description="Invalid request")
    
    if ('goal' not in data):
        abort(400, description="Please fill out the form!")
    
    # Determine if a new macrocycle should be made instead of changing the current one.
    if (request.method == 'POST'):
        alter_old = False
    else:
        alter_old = True

    state = {
        "user_id": current_user.id,
        "macrocycle_impacted": True,
        "macrocycle_is_altered": True,
        "macrocycle_message": data.get("goal", ""),
        "macrocycle_alter_old": alter_old
    }
    goal_agent = create_goal_agent()

    result = goal_agent.invoke(state)
    return jsonify({"status": "success", "macrocycles": result}), 200

# Change the current user's macrocycle by the id (doesn't restrict what can be assigned).
@bp.route('/<goal_id>', methods=['POST', 'PATCH'])
@login_required
def change_macrocycle_by_id(goal_id):
    macrocycles = MacrocycleActions.change_by_id(goal_id)
    return jsonify({"status": "success", "macrocycles": macrocycles}), 200

# ---------- TEST ROUTES --------------

# Testing for goal classification.
@bp.route('/test', methods=['GET', 'POST'])
def goal_classification_test():
    result = []
    goal_types = retrieve_goal_types()
    goal_app = create_goal_classification_graph()
    
    user_goals = [
        "Create a new user equipment for my new barbell that weighs 4 kilograms.",
        "I would like to do a push up.",
        "I would like to be ready for the soccer championship.",
        "Am I ready for the soccker championship this year?",
        "I would like to weight 100 pounds."
        ]

    for user_goal in user_goals:
        result.append(goal_classification_test_run(goal_app, goal_types, user_goal))

    return jsonify({"status": "success", "test_results": result}), 200

