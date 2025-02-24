from flask import request, jsonify, Blueprint

from app.models import Goal_Library

bp = Blueprint('goals', __name__)

from app.agents.goals import goal_app

# ----------------------------------------- Goals -----------------------------------------

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

# Testing for goal classification.
@bp.route('/goal_classification', methods=['GET'])
def goal_classification():
    results = {}
    
    user_goal = "Create a new user equipment for my new barbell that weighs 4 kilograms."
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_1"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")

    
    user_goal = "I would like to do a push up."
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_2"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")

    user_goal = "I would like to be ready for the soccer championship."
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_3"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")
    

    user_goal = "Am I ready for the soccker championship this year?"
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_4"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")

    user_goal = "I would like to weight 100 pounds."
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_5"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")
    
    return jsonify(results), 200

