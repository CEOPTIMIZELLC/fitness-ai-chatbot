from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from flask import abort
from datetime import timedelta
from langgraph.graph import StateGraph, START, END
from app.main_agent.user_macrocycles import create_goal_agent


from app import db
from app.models import User_Mesocycles, User_Macrocycles

from app.agents.phases import Main as phase_main
from app.utils.common_table_queries import current_macrocycle, current_mesocycle

from app.main_agent.utils import construct_phases_list
from app.main_agent.utils import print_mesocycles_schedule
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class AgentState(MainAgentState):
    user_macrocycle: any
    macrocycle_id: int
    goal_id: int
    start_date: any
    macrocycle_allowed_weeks: int
    possible_phases: list
    agent_output: list
    sql_models: any

# Confirm that the desired section should be impacted.
def confirm_impact(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Changing User Mesocycle=========")
    if verbose_subagent_steps:
        print(f"---------Confirm that the User Mesocycle is Impacted---------")
    if not state["mesocycle_impacted"]:
        if verbose_subagent_steps:
            print(f"---------No Impact---------")
        return "no_impact"
    return "impact"

# Retrieve parent item that will be used for the current schedule.
def retrieve_parent(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Current Macrocycle---------")
    user_id = state["user_id"]
    user_macrocycle = current_macrocycle(user_id)
    return {"user_macrocycle": user_macrocycle}

# Confirm that a currently active parent exists to attach the a schedule to.
def confirm_parent(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Confirm there is an active Macrocycle---------")
    if not state["user_macrocycle"]:
        return "no_parent"
    return "parent"

# Request permission from user to execute the parent initialization.
def ask_for_permission(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Ask user if a new Macrocycle can be made---------")
    return {
        "macrocycle_impacted": True,
        "macrocycle_message": "I would like to lose 20 pounds."
    }

# Router for if permission was granted.
def confirm_permission(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Confirm the agent can create a new Macrocycle---------")
    if not state["macrocycle_impacted"]:
        return "permission_denied"
    return "permission_granted"

# State if the Macrocycle isn't allowed to be requested.
def permission_denied(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Abort Mesocycle Scheduling---------")
    abort(404, description="No active macrocycle found.")
    return {}

def macrocycle_node(state: AgentState):
    print(f"\n---------Changing User Macrocycle---------")
    if state["macrocycle_impacted"]:
        goal_agent = create_goal_agent()
        result = goal_agent.invoke({
            "user_id": state["user_id"], 
            "user_input": state["user_input"], 
            "attempts": state["attempts"], 
            "macrocycle_impacted": state["macrocycle_impacted"], 
            "macrocycle_message": state["macrocycle_message"], 
            "macrocycle_formatted": state["macrocycle_formatted"]
        })
    else:
        result = {
            "macrocycle_message": None, 
            "macrocycle_formatted": None
        }
    return {
        "macrocycle_message": result["macrocycle_message"], 
        "macrocycle_formatted": result["macrocycle_formatted"]
    }

# Retrieve necessary information for the schedule creation.
def retrieve_information(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Information for Mesocycle Scheduling---------")
    user_macrocycle = state["user_macrocycle"]
    macrocycle_id = user_macrocycle.id
    goal_id = user_macrocycle.goal_id
    start_date = user_macrocycle.start_date
    macrocycle_allowed_weeks = macrocycle_weeks
    possible_phases = construct_phases_list(int(goal_id))
    return {
        "macrocycle_id": macrocycle_id,
        "goal_id": goal_id,
        "start_date": start_date,
        "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
        "possible_phases": possible_phases
    }

# Delete the old items belonging to the parent.
def delete_old_children(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Delete old Mesocycles---------")
    macrocycle_id = state["macrocycle_id"]
    db.session.query(User_Mesocycles).filter_by(macrocycle_id=macrocycle_id).delete()
    if verbose:
        print("Successfully deleted")
    return {}

# Executes the agent to create the mesocycle/phase schedule for the current macrocycle.
def perform_phase_selection(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Perform Mesocycle Scheduling---------")
    goal_id = state["goal_id"]
    macrocycle_allowed_weeks = state["macrocycle_allowed_weeks"]
    parameters={
        "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
        "goal_type": goal_id}
    constraints={}

    # Retrieve all possible phases that can be selected and convert them into a list form.
    parameters["possible_phases"] = construct_phases_list(int(goal_id))

    result = phase_main(parameters, constraints)

    if verbose:
        print(result["formatted"])
    return {
        "agent_output": result["output"]
    }

# Convert output from the agent to SQL models.
def agent_output_to_sqlalchemy_model(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Convert schedule to SQLAlchemy models.---------")
    phases_output = state["agent_output"]
    macrocycle_id = state["macrocycle_id"]
    mesocycle_start_date = state["start_date"]

    # Convert output to form that may be stored.
    user_phases = []
    order = 1
    for phase in phases_output:
        new_phase = User_Mesocycles(
            macrocycle_id = macrocycle_id,
            phase_id = phase["id"],
            is_goal_phase = phase["is_goal_phase"],
            order = order,
            start_date = mesocycle_start_date,
            end_date = mesocycle_start_date + timedelta(weeks=phase["duration"])
        )
        user_phases.append(new_phase)

        # Set startdate of next phase to be at the end of the current one.
        mesocycle_start_date +=timedelta(weeks=phase["duration"])
        order += 1

    db.session.add_all(user_phases)
    db.session.commit()
    return {"sql_models": user_phases}

# Print output.
def get_formatted_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Formatted Schedule for user---------")
    user_macrocycle = state["user_macrocycle"]

    user_mesocycles = user_macrocycle.mesocycles
    if not user_mesocycles:
        abort(404, description="No mesocycles found for the macrocycle.")

    user_mesocycles_dict = [user_mesocycle.to_dict() for user_mesocycle in user_mesocycles]

    formatted_schedule = print_mesocycles_schedule(user_mesocycles_dict)
    if verbose_formatted_schedule:
        print(formatted_schedule)
    return {"mesocycle_formatted": formatted_schedule}

# Retrieve current user's mesocycles
def get_user_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving All Mesocycles for User---------")
    user_id = state["user_id"]
    user_mesocycles = User_Mesocycles.query.join(User_Macrocycles).filter_by(user_id=user_id).all()
    return [user_mesocycle.to_dict() 
            for user_mesocycle in user_mesocycles]

# Retrieve user's current macrocycles's mesocycles
def get_user_current_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Current Mesocycles for User---------")
    user_macrocycle = state["user_macrocycle"]
    user_mesocycles = user_macrocycle.mesocycles
    return [user_mesocycle.to_dict() 
            for user_mesocycle in user_mesocycles]


# Retrieve user's current mesocycle
def read_user_current_element(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Current Mesocycle for User---------")
    user_id = state["user_id"]
    user_mesocycle = current_mesocycle(user_id)
    if not user_mesocycle:
        abort(404, description="No active mesocycle found.")
    return user_mesocycle.to_dict()

# Create main agent.
def create_main_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve_parent", retrieve_parent)
    workflow.add_node("ask_for_permission", ask_for_permission)
    workflow.add_node("permission_denied", permission_denied)
    workflow.add_node("macrocycle", macrocycle_node)
    workflow.add_node("retrieve_information", retrieve_information)
    workflow.add_node("delete_old_children", delete_old_children)
    workflow.add_node("perform_phase_selection", perform_phase_selection)
    workflow.add_node("agent_output_to_sqlalchemy_model", agent_output_to_sqlalchemy_model)
    workflow.add_node("get_formatted_list", get_formatted_list)

    workflow.add_conditional_edges(
        START,
        confirm_impact,
        {
            "no_impact": END,
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
            "permission_granted": "macrocycle"
        }
    )
    workflow.add_edge("macrocycle", "retrieve_parent")

    workflow.add_edge("retrieve_information", "delete_old_children")
    workflow.add_edge("delete_old_children", "perform_phase_selection")
    workflow.add_edge("perform_phase_selection", "agent_output_to_sqlalchemy_model")
    workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
    workflow.add_edge("permission_denied", END)
    workflow.add_edge("get_formatted_list", END)

    return workflow.compile()
