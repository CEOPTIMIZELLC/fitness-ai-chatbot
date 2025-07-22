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

def new_macrocycle(user_id, goal_id, new_goal):
    new_macrocycle = User_Macrocycles(user_id=user_id, goal_id=goal_id, goal=new_goal)
    db.session.add(new_macrocycle)
    db.session.commit()
    return new_macrocycle

def alter_macrocycle(macrocycle_id, goal_id, new_goal):
    user_macrocycle = db.session.get(User_Macrocycles, macrocycle_id)
    user_macrocycle.goal = new_goal
    user_macrocycle.goal_id = goal_id
    db.session.commit()
    return user_macrocycle

def which_operation(goal, request_method):
    user_id = current_user.id
    # Change the current user's macrocycle and the goal type if a new one can be assigned.
    if goal["goal_id"]:
        # Add a new macrocycle if posting.
        if (request_method == 'POST'):
            new_macrocycle(user_id, goal["goal_id"], goal["new_goal"])
        else:
            user_macro = current_macrocycle(user_id)
            alter_macrocycle(user_macro.id, goal["goal_id"], goal["new_goal"])

    return {
        "new_goal": goal["new_goal"],
        "goal_classification": goal["goal_class"],
        "goal_id": goal["goal_id"]}