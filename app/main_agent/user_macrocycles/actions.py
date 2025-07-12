from flask import request, abort
from flask_login import current_user

from app import db
from app.models import Goal_Library, User_Macrocycles

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

def which_operation(goal, request_method):
    # Change the current user's macrocycle and the goal type if a new one can be assigned.
    if goal["goal_id"]:
        # Add a new macrocycle if posting.
        if (request_method == 'POST'):
            new_macrocycle(goal["goal_id"], goal["new_goal"])
        else:
            alter_macrocycle(goal["goal_id"], goal["new_goal"])

    return {
        "new_goal": goal["new_goal"],
        "goal_classification": goal["goal_class"],
        "goal_id": goal["goal_id"]}

class MacrocycleActions:
    # Retrieve current user's macrocycles
    @staticmethod
    def get_user_list():
        user_macros = current_user.macrocycles
        return [macrocycle.to_dict() 
                for macrocycle in user_macros]

    # Retrieve current user's macrocycles
    @staticmethod
    def read_user_current_element():
        user_macro = current_macrocycle(current_user.id)
        if not user_macro:
            abort(404, description="No active macrocycle found.")
        return user_macro.to_dict()

    # Change the current user's macrocycle.
    @staticmethod
    def scheduler(new_goal):
        # There are only so many goal types a macrocycle can be classified as, with all of them being stored.
        goal_types = retrieve_goal_types()
        goal_app = create_goal_classification_graph()

        # Invoke with new macrocycle and possible goal types.
        state = goal_app.invoke({
            "new_goal": new_goal, 
            "goal_types": goal_types, 
            "attempts": 0})
        
        # Change the current user's macrocycle and the goal type if a new one can be assigned.
        return which_operation(state, request.method)

    # Change the current user's macrocycle by the id (doesn't restrict what can be assigned).
    @staticmethod
    def change_by_id(goal_id):
        # Ensure that id is possible.
        goal = db.session.get(Goal_Library, goal_id)
        if not goal:
            abort(404, description=f"Goal {goal_id} not found.")

        state = {
            "new_goal": f"Goal of {goal_id}",
            "goal_class": goal.name,
            "goal_id": goal_id}

        # Change the current user's macrocycle and the goal type if a new one can be assigned.
        return which_operation(state, request.method)
