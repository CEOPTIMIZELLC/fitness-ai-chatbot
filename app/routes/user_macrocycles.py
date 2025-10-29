from logging_config import LogRoute
from flask import jsonify

from app import db
from app.models import Goal_Library

from app.solver_agents.goals import create_goal_classification_graph
from app.main_sub_agents.user_macrocycles import create_goal_agent as create_agent

from app.database_to_frontend.user_macrocycles import ItemRetriever, CurrentRetriever

from .blueprint_factories.subagent_items import create_item_blueprint

# ----------------------------------------- User Macrocycles -----------------------------------------

item_name = "user_macrocycles"
focus_name = "macrocycle"

bp = create_item_blueprint(
    item_name, focus_name, request_name = "goal", 
    item_retriever = ItemRetriever, 
    current_retriever = CurrentRetriever, 
    create_agent = create_agent, 
    add_test_retrievers = True, 
    add_initializers = True
)

# ---------- TEST ROUTES --------------

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
    LogRoute.verbose(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    LogRoute.verbose("")
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

    return jsonify({"status": "success", "response": result}), 200

