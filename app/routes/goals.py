from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Goal_Library

bp = Blueprint('goals', __name__)

from app.agents.goals import create_goal_classification_graph

# ----------------------------------------- Goals -----------------------------------------
# Retrieve possible goal types.
def retrieve_goal_types():
    goals = (
        db.session.query(
            Goal_Library.id,
            Goal_Library.name
        )
        .all()
    )

    return [
        {
            "id": goal.id, 
            "name": goal.name.lower()
        } 
        for goal in goals
    ]

# Retrieve goals
@bp.route('/', methods=['GET'])
def get_goal_list():
    goals = Goal_Library.query.all()
    result = []
    for goal in goals:
        result.append(goal.to_dict())
    return jsonify({"status": "success", "goals": result}), 200

# Show goals based on id.
@bp.route('/<goal_id>', methods=['GET'])
def read_goal(goal_id):
    goal = Goal_Library.query.filter_by(id=goal_id).first()
    if not goal:
        return jsonify({"status": "error", "message": "Goal " + goal_id + " not found."}), 404
    return jsonify(goal.to_dict()), 200

# Change the current user's goal.
@bp.route('/change_goal', methods=['POST', 'PATCH'])
@login_required
def change_goal():
    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    
    # Ensure that a goal has been provided.
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
        current_user.goal = state["new_goal"]
        current_user.goal_id = state["goal_id"]
        db.session.commit()

    return jsonify({
        "new_goal": state["new_goal"],
        "goal_classification": state["goal_class"],
        "goal_id": state["goal_id"]
    }), 200


# Testing for goal classification.
@bp.route('/goal_classification_test', methods=['GET', 'POST'])
def goal_classification_test():
    results = {}
    goal_types = retrieve_goal_types()
    goal_app = create_goal_classification_graph()
    
    user_goal = "Create a new user equipment for my new barbell that weighs 4 kilograms."
    result_temp = goal_app.invoke(
        {
            "new_goal": user_goal, 
            "goal_types": goal_types, 
            "attempts": 0
        })
    results["result_1"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")


    user_goal = "I would like to do a push up."
    result_temp = goal_app.invoke(
        {
            "new_goal": user_goal, 
            "goal_types": goal_types, 
            "attempts": 0
        })
    results["result_2"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")

    user_goal = "I would like to be ready for the soccer championship."
    result_temp = goal_app.invoke(
        {
            "new_goal": user_goal, 
            "goal_types": goal_types, 
            "attempts": 0
        })
    results["result_3"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")
    

    user_goal = "Am I ready for the soccker championship this year?"
    result_temp = goal_app.invoke(
        {
            "new_goal": user_goal, 
            "goal_types": goal_types, 
            "attempts": 0
        })
    results["result_4"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")

    user_goal = "I would like to weight 100 pounds."
    result_temp = goal_app.invoke(
        {
            "new_goal": user_goal, 
            "goal_types": goal_types, 
            "attempts": 0
        })
    results["result_5"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")
    
    return jsonify(results), 200

