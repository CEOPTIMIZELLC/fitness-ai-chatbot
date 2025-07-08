from config import verbose, verbose_formatted_schedule, verbose_agent_introductions
from flask import abort
from datetime import timedelta
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


from app import db
from app.models import User_Macrocycles

from app.agents.goals import create_goal_classification_graph
from app.utils.common_table_queries import current_macrocycle

from .actions import retrieve_goal_types
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class AgentState(MainAgentState):
    goal_id: int
    alter_old: bool

# Confirm that the desired section should be impacted.
def confirm_impact(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Changing User Macrocycle=========")
    print(f"---------Confirm that the User Macrocycle is Impacted---------")
    if not state["macrocycle_impacted"]:
        return "no_impact"
    return "impact"

# In between node for chained conditional edges.
def impact_confirmed(state: AgentState):
    return {}

def confirm_new_goal(state: AgentState):
    print(f"---------Confirm there is a goal to be classified---------")
    if not state["macrocycle_message"]:
        return "no_goal"
    return "present_goal"

def ask_for_permission(state: AgentState):
    print(f"---------Ask user for a new goal---------")
    return {
        "macrocycle_impacted": True,
        "macrocycle_message": "I would like to lose 20 pounds."
    }

# State if the goal isn't requested.
def no_goal_requested(state: AgentState):
    print(f"---------Abort Goal Classifier---------")
    abort(404, description="No goal requested.")
    return {}

def perform_goal_classifier(state: AgentState):
    print(f"---------Perform Goal Classifier---------")
    new_goal = state["macrocycle_message"]
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
    new_goal = state["macrocycle_message"]
    new_macrocycle = User_Macrocycles(user_id=user_id, goal_id=goal_id, goal=new_goal)
    db.session.add(new_macrocycle)
    db.session.commit()
    return {}

def alter_macrocycle(state: AgentState):
    user_id = state["user_id"]
    goal_id = state["goal_id"]
    new_goal = state["macrocycle_message"]
    user_macrocycle = current_macrocycle(user_id)
    user_macrocycle.goal = new_goal
    user_macrocycle.goal_id = goal_id
    db.session.commit()
    return {}

def get_formatted_list(state: AgentState):
    print(f"---------Retrieving Formatted Schedule for user---------")
    macrocycle_message = state["macrocycle_message"]
    if verbose_formatted_schedule:
        print(macrocycle_message)
    return {"macrocycle_formatted": macrocycle_message}

def create_main_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("impact_confirmed", impact_confirmed)
    workflow.add_node("ask_for_permission", ask_for_permission)
    workflow.add_node("perform_goal_classifier", perform_goal_classifier)
    workflow.add_node("new_macrocycle", new_macrocycle)
    workflow.add_node("alter_macrocycle", alter_macrocycle)
    workflow.add_node("get_formatted_list", get_formatted_list)
    workflow.add_node("no_goal_requested", no_goal_requested)

    workflow.add_conditional_edges(
        START,
        confirm_impact,
        {
            "no_impact": END,
            "impact": "impact_confirmed"
        }
    )

    workflow.add_conditional_edges(
        "impact_confirmed",
        confirm_new_goal,
        {
            "no_goal": "ask_for_permission",
            "present_goal": "perform_goal_classifier"
        }
    )

    workflow.add_conditional_edges(
        "ask_for_permission",
        confirm_new_goal,
        {
            "no_goal": "no_goal_requested",
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

    workflow.add_edge("alter_macrocycle", "get_formatted_list")
    workflow.add_edge("new_macrocycle", "get_formatted_list")
    workflow.add_edge("no_goal_requested", END)
    workflow.add_edge("get_formatted_list", END)

    return workflow.compile()
