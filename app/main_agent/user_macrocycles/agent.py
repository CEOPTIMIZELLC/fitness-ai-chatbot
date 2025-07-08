from config import verbose, verbose_formatted_schedule, verbose_agent_introductions
from flask import abort
from datetime import timedelta
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


from app import db
from app.models import User_Macrocycles, User_Mesocycles

from app.agents.goals import create_goal_classification_graph
from app.utils.common_table_queries import current_macrocycle

from .actions import retrieve_goal_types
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class AgentState(MainAgentState):
    user_macrocycle: any
    goal_id: int
    alter_old: bool

# Confirm that the desired section should be impacted.
def confirm_impact(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Changing User Macrocycle=========")
    print(f"---------Confirm that the User Macrocycle is Impacted---------")
    if not state["macrocycle_impacted"]:
        print(f"---------No Impact---------")
        return "no_impact"
    return "impact"

# In between node for chained conditional edges.
def impact_confirmed(state: AgentState):
    return {}

# Check if a new goal exists to be classified.
def confirm_new_goal(state: AgentState):
    print(f"---------Confirm there is a goal to be classified---------")
    if not state["macrocycle_message"]:
        return "no_goal"
    return "present_goal"

# Ask user for a new goal if one isn't in the initial request.
def ask_for_new_goal(state: AgentState):
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

# Classify the new goal in one of the possible goal types.
def perform_goal_classifier(state: AgentState):
    print(f"---------Perform Goal Classifier---------")
    new_goal = state["macrocycle_message"]
    # There are only so many goal types a macrocycle can be classified as, with all of them being stored.
    goal_types = retrieve_goal_types()
    goal_app = create_goal_classification_graph()

    user_id = state["user_id"]
    user_macrocycle = current_macrocycle(user_id)

    # Invoke with new macrocycle and possible goal types.
    goal = goal_app.invoke({
        "new_goal": new_goal, 
        "goal_types": goal_types, 
        "attempts": 0})
    
    return {
        "user_macrocycle": user_macrocycle,
        "goal_id": goal["goal_id"],
        "alter_old": True
    }

# Determine whether the current macrocycle should be edited or if a new one should be created.
def which_operation(state: AgentState):
    print(f"---------Determine whether goal should be new---------")
    if state["alter_old"] and state["user_macrocycle"]:
        return "alter_macrocycle"
    return "create_new_macrocycle"

# Creates the new macrocycle of the determined type.
def create_new_macrocycle(state: AgentState):
    user_id = state["user_id"]
    goal_id = state["goal_id"]
    new_goal = state["macrocycle_message"]
    new_macrocycle = User_Macrocycles(user_id=user_id, goal_id=goal_id, goal=new_goal)
    db.session.add(new_macrocycle)
    db.session.commit()
    return {"user_macrocycle": new_macrocycle}

# Delete the old items belonging to the parent.
def delete_old_children(state: AgentState):
    print(f"---------Delete old items of current Macrocycle---------")
    macrocycle_id = state["user_macrocycle"].id
    db.session.query(User_Mesocycles).filter_by(macrocycle_id=macrocycle_id).delete()
    if verbose:
        print("Successfully deleted")
    return {}

# Alters the current macrocycle to be the determined type.
def alter_macrocycle(state: AgentState):
    goal_id = state["goal_id"]
    new_goal = state["macrocycle_message"]
    user_macrocycle = state["user_macrocycle"]
    user_macrocycle.goal = new_goal
    user_macrocycle.goal_id = goal_id
    db.session.commit()
    return {"user_macrocycle": user_macrocycle}

# Print output.
def get_formatted_list(state: AgentState):
    print(f"---------Retrieving Formatted Schedule for user---------")
    macrocycle_message = state["macrocycle_message"]
    if verbose_formatted_schedule:
        print(macrocycle_message)
    return {"macrocycle_formatted": macrocycle_message}

# Create main agent.
def create_main_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("impact_confirmed", impact_confirmed)
    workflow.add_node("ask_for_new_goal", ask_for_new_goal)
    workflow.add_node("perform_goal_classifier", perform_goal_classifier)
    workflow.add_node("create_new_macrocycle", create_new_macrocycle)
    workflow.add_node("delete_old_children", delete_old_children)
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
            "no_goal": "ask_for_new_goal",
            "present_goal": "perform_goal_classifier"
        }
    )

    workflow.add_conditional_edges(
        "ask_for_new_goal",
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
            "alter_macrocycle": "delete_old_children",
            "create_new_macrocycle": "create_new_macrocycle"
        }
    )

    workflow.add_edge("delete_old_children", "alter_macrocycle")
    workflow.add_edge("alter_macrocycle", "get_formatted_list")
    workflow.add_edge("create_new_macrocycle", "get_formatted_list")
    workflow.add_edge("no_goal_requested", END)
    workflow.add_edge("get_formatted_list", END)

    return workflow.compile()
