from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from flask import abort
from datetime import timedelta
from langgraph.graph import StateGraph, START, END
from app.main_agent.user_mesocycles import create_mesocycle_agent


from app import db
from app.models import User_Microcycles, User_Mesocycles

from app.utils.common_table_queries import current_mesocycle, current_microcycle
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Microcycles -----------------------------------------

class AgentState(MainAgentState):
    user_mesocycle: any
    mesocycle_id: int
    microcycle_count: int
    microcycle_duration: any
    start_date: any

# Confirm that the desired section should be impacted.
def confirm_impact(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Starting User Microcycle=========")
    if verbose_subagent_steps:
        print(f"\t---------Confirm that the User Microcycle is Impacted---------")
    if not state["microcycle_impacted"]:
        if verbose_subagent_steps:
            print(f"\t---------No Impact---------")
        return "no_impact"
    return "impact"

# Retrieve parent item that will be used for the current schedule.
def retrieve_parent(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving Current Mesocycle---------")
    user_id = state["user_id"]
    user_mesocycle = current_mesocycle(user_id)

    # Return parent.
    return {"user_mesocycle": user_mesocycle.to_dict() if user_mesocycle else None}

# Confirm that a currently active parent exists to attach the a schedule to.
def confirm_parent(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Confirm there is an active Mesocycle---------")
    if not state["user_mesocycle"]:
        return "no_parent"
    return "parent"

# Request permission from user to execute the parent initialization.
def ask_for_permission(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Ask user if a new Mesocycle can be made---------")
    return {
        "mesocycle_impacted": True,
        "mesocycle_message": "I would like to lose 20 pounds."
    }

# Router for if permission was granted.
def confirm_permission(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Confirm the agent can create a new Mesocycle---------")
    if not state["mesocycle_impacted"]:
        return "permission_denied"
    return "permission_granted"

# State if the Macrocycle isn't allowed to be requested.
def permission_denied(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Abort Microcycle Scheduling---------")
    abort(404, description="No active mesocycle found.")
    return {}

# Retrieve necessary information for the schedule creation.
def retrieve_information(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving Information for Microcycle Scheduling---------")
    user_mesocycle = state["user_mesocycle"]

    # Each microcycle must last 1 week.
    microcycle_duration = timedelta(weeks=1)

    # Find how many one week microcycles will be present in the mesocycle
    microcycle_count = user_mesocycle["duration_days"] // microcycle_duration.days
    microcycle_start = user_mesocycle["start_date"]

    return {
        "mesocycle_id": user_mesocycle["id"],
        "microcycle_duration": microcycle_duration,
        "microcycle_count": microcycle_count,
        "start_date": microcycle_start
    }

# Delete the old items belonging to the parent.
def delete_old_children(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Delete old Microcycles---------")
    mesocycle_id = state["mesocycle_id"]
    db.session.query(User_Microcycles).filter_by(mesocycle_id=mesocycle_id).delete()
    if verbose:
        print("Successfully deleted")
    return {}

# Initializes the microcycle schedule for the current mesocycle.
def perform_microcycle_initialization(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Perform Microcycle Scheduling---------")
    mesocycle_id = state["mesocycle_id"]
    microcycle_duration = state["microcycle_duration"]
    microcycle_count = state["microcycle_count"]
    microcycle_start = state["start_date"]

    # Create a microcycle for each week in the mesocycle.
    microcycles = []
    for i in range(microcycle_count):
        microcycle_end = microcycle_start + microcycle_duration
        new_microcycle = User_Microcycles(
            mesocycle_id = mesocycle_id,
            order = i+1,
            start_date = microcycle_start,
            end_date = microcycle_end,
        )

        microcycles.append(new_microcycle)

        # Shift the start of the next microcycle to be the end of the current.
        microcycle_start = microcycle_end

    db.session.add_all(microcycles)
    db.session.commit()

    return {}

# Print output.
def get_formatted_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving Formatted Schedule for user---------")
    user_id = state["user_id"]
    user_mesocycle = current_mesocycle(user_id)

    user_microcycles = user_mesocycle.microcycles
    if not user_microcycles:
        abort(404, description="No microcycles found for the mesocycle.")

    user_microcycles_dict = [user_microcycle.to_dict() for user_microcycle in user_microcycles]
    
    # Create a stringified version of the schedule.
    formatted_schedule = "\n"
    for user_microcycle in user_microcycles_dict:
        formatted_schedule += f"Microcycle {user_microcycle["order"]}: {user_microcycle["start_date"]} - {user_microcycle["end_date"]} ({user_microcycle["duration"]})\n"

    if verbose_formatted_schedule:
        print(formatted_schedule)
    return {"microcycle_formatted": formatted_schedule}

# Retrieve current user's microcycles
def get_user_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving All Microcycles for User---------")
    user_id = state["user_id"]
    user_microcycles = User_Microcycles.query.join(User_Mesocycles).filter_by(user_id=user_id).all()
    return [user_microcycle.to_dict() 
            for user_microcycle in user_microcycles]

# Retrieve user's current mesocycles's microcycles
def get_user_current_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving Current Microcycles for User---------")
    user_id = state["user_id"]
    user_mesocycle = current_mesocycle(user_id)
    user_microcycles = user_mesocycle.microcycles
    return [user_microcycle.to_dict() 
            for user_microcycle in user_microcycles]

# Retrieve user's current microcycle
def read_user_current_element(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving Current Microcycle for User---------")
    user_id = state["user_id"]
    user_microcycle = current_microcycle(user_id)
    if not user_microcycle:
        abort(404, description="No active microcycle found.")
    return user_microcycle.to_dict()

# Node to declare that the sub agent has ended.
def end_node(state: AgentState):
    if verbose_agent_introductions:
        print(f"=========Ending User Microcycle=========\n")
    return {}

# Create main agent.
def create_main_agent_graph():
    workflow = StateGraph(AgentState)
    mesocycle_agent = create_mesocycle_agent()

    workflow.add_node("retrieve_parent", retrieve_parent)
    workflow.add_node("ask_for_permission", ask_for_permission)
    workflow.add_node("permission_denied", permission_denied)
    workflow.add_node("mesocycle", mesocycle_agent)
    workflow.add_node("retrieve_information", retrieve_information)
    workflow.add_node("delete_old_children", delete_old_children)
    workflow.add_node("perform_microcycle_initialization", perform_microcycle_initialization)
    workflow.add_node("get_formatted_list", get_formatted_list)
    workflow.add_node("end_node", end_node)

    workflow.add_conditional_edges(
        START,
        confirm_impact,
        {
            "no_impact": "end_node",
            "impact": "retrieve_parent"
        }
    )

    workflow.add_conditional_edges(
        "retrieve_parent",
        confirm_parent,
        {
            "no_parent": "ask_for_permission",
            "parent": "retrieve_information"
        }
    )

    workflow.add_conditional_edges(
        "ask_for_permission",
        confirm_permission,
        {
            "permission_denied": "permission_denied",
            "permission_granted": "mesocycle"
        }
    )
    workflow.add_edge("mesocycle", "retrieve_parent")

    workflow.add_edge("retrieve_information", "delete_old_children")
    workflow.add_edge("delete_old_children", "perform_microcycle_initialization")
    workflow.add_edge("perform_microcycle_initialization", "get_formatted_list")
    workflow.add_edge("permission_denied", "end_node")
    workflow.add_edge("get_formatted_list", "end_node")
    workflow.add_edge("end_node", END)

    return workflow.compile()
