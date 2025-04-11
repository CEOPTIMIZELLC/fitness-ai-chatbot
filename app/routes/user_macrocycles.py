from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Goal_Library, User_Macrocycles

bp = Blueprint('user_macrocycles', __name__)

from app.agents.goals import create_goal_classification_graph
from app.utils.common_table_queries import current_macrocycle

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

def new_macrocycle(goal_id, new_goal):
    new_macro = User_Macrocycles(user_id=current_user.id, goal_id=goal_id, goal=new_goal)
    db.session.add(new_macro)
    db.session.commit()

def alter_macrocycle(goal_id, new_goal):
    user_macro = current_macrocycle(current_user.id)
    user_macro.goal = new_goal
    user_macro.goal_id = goal_id
    db.session.commit()

# Retrieve current user's goals
@bp.route('/', methods=['GET'])
@login_required
def get_user_goal():
    user_macros = current_user.macrocycles
    result = []
    for goal in user_macros:
        result.append(goal.to_dict())
    return jsonify({"status": "success", "goals": result}), 200


# Retrieve current user's goals
@bp.route('/current', methods=['GET'])
@login_required
def get_user_current_macrocycle():
    user_macro = current_macrocycle(current_user.id)
    if not user_macro:
        return jsonify({"status": "error", "message": "No active goal found."}), 404
    return jsonify({"status": "success", "goals": user_macro.to_dict()}), 200

# Change the current user's goal.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def change_goal():
    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    
    if ('goal' not in data):
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400
    
    # There are only so many types a goal can be classified as, with all of them being stored.
    goal_types = retrieve_goal_types()
    goal_app = create_goal_classification_graph()

    # Invoke with new goal and possible goal types.
    state = goal_app.invoke(
        {
            "new_goal": data.get("goal", ""), 
            "goal_types": goal_types, 
            "attempts": 0
        })
    
    # Change the current user's goal and the goal type if a new one can be assigned.
    if state["goal_id"]:
        # Add a new goal if posting.
        if (request.method == 'POST'):
            new_macrocycle(state["goal_id"], state["new_goal"])
        else:
            alter_macrocycle(state["goal_id"], state["new_goal"])

    return jsonify({
        "new_goal": state["new_goal"],
        "goal_classification": state["goal_class"],
        "goal_id": state["goal_id"]
    }), 200


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
    
    return jsonify(result), 200

