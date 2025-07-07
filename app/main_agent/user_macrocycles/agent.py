from config import verbose, verbose_formatted_schedule
from flask import abort
from datetime import timedelta
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


from app import db
from app.models import User_Macrocycles

from app.agents.goals import create_goal_classification_graph
from app.utils.common_table_queries import current_macrocycle

from .actions import retrieve_goal_types

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class AgentState(TypedDict):
    user_id: int
    new_goal: str
    check: bool
    attempts: int
    goal_id: int
    alter_old: bool


def confirm_new_goal(state: AgentState):
    print(f"---------Confirm there is a goal to be classified---------")
    if not state["new_goal"]:
        return "no_goal"
    return "present_goal"

def ask_for_permission(state: AgentState):
    print(f"---------Ask user for a new goal---------")
    abort(404, description="No goal requested.")
    return {}

def perform_goal_classifier(state: AgentState):
    print(f"---------Perform Goal Classifier---------")
    new_goal = state["new_goal"]
    # There are only so many goal types a macrocycle can be classified as, with all of them being stored.
    goal_types = retrieve_goal_types()
    goal_app = create_goal_classification_graph()

    # Invoke with new macrocycle and possible goal types.
    goal = goal_app.invoke({
        "new_goal": new_goal, 
        "goal_types": goal_types, 
        "attempts": 0})
    
    return {"goal_id": goal["goal_id"],
            "alter_old": False}

def which_operation(state: AgentState):
    print(f"---------Determine whether goal should be new---------")
    if state["alter_old"]:
        return "alter_macrocycle"
    return "new_macrocycle"

def new_macrocycle(state: AgentState):
    user_id = state["user_id"]
    goal_id = state["goal_id"]
    new_goal = state["new_goal"]
    new_macrocycle = User_Macrocycles(user_id=user_id, goal_id=goal_id, goal=new_goal)
    db.session.add(new_macrocycle)
    db.session.commit()
    return {}

def alter_macrocycle(state: AgentState):
    user_id = state["user_id"]
    goal_id = state["goal_id"]
    new_goal = state["new_goal"]
    user_macrocycle = current_macrocycle(user_id)
    user_macrocycle.goal = new_goal
    user_macrocycle.goal_id = goal_id
    db.session.commit()
    return {}

def create_main_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("ask_for_permission", ask_for_permission)
    workflow.add_node("perform_goal_classifier", perform_goal_classifier)
    workflow.add_node("new_macrocycle", new_macrocycle)
    workflow.add_node("alter_macrocycle", alter_macrocycle)

    workflow.add_conditional_edges(
        START,
        confirm_new_goal,
        {
            "no_goal": "ask_for_permission",
            "present_goal": "perform_goal_classifier"
        }
    )

    workflow.add_conditional_edges(
        "perform_goal_classifier",
        which_operation,
        {
            "alter_macrocycle": "alter_macrocycle",
            "new_macrocycle": "new_macrocycle"
        }
    )

    workflow.add_edge("ask_for_permission", END)
    workflow.add_edge("alter_macrocycle", END)
    workflow.add_edge("new_macrocycle", END)

    return workflow.compile()
