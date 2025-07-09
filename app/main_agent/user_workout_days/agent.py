from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from flask import abort
from langgraph.graph import StateGraph, START, END
from app.main_agent.user_microcycles import create_microcycle_agent
from app.main_agent.user_weekdays_availability import create_availability_agent

from app import db
from app.models import User_Workout_Components, User_Workout_Days, Bodypart_Library, Phase_Component_Library

from app.agents.phase_components import Main as phase_component_main
from app.utils.common_table_queries import current_microcycle

from .actions import duration_to_weekdays, retrieve_availability_for_week, retrieve_weekday_availability_information_from_availability, retrieve_pc_parameters

from app.main_agent.utils import print_workout_days_schedule

from app.utils.print_long_output import print_long_output
from app.utils.db_helpers import get_all_items
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Workout Days -----------------------------------------

class AgentState(MainAgentState):
    user_microcycle: any
    microcycle_id: int
    phase_id: int
    duration: any

    microcycle_weekdays: list
    user_workdays: list

    user_availability: any
    weekday_availability: list
    number_of_available_weekdays: int
    total_availability: int

    start_date: any
    agent_output: list
    sql_models: any


# Confirm that a currently active prerequisite exists to attach the a schedule to.
def confirm_prerequisites(state, key_to_check, log_title):
    if verbose_subagent_steps:
        print(f"---------Confirm there is an active {log_title}---------")
    if not state[key_to_check]:
        return "no_parent"
    return "parent"

# Request permission from user to execute the prerequisite initialization.
def ask_for_permission(state, checked_item, log_title):
    if verbose_subagent_steps:
        print(f"---------Ask user if a new {log_title} can be made---------")
    if checked_item == "availability":
        new_message = "I should have 30 minutes every day now."
    else:
        new_message = "I would like to lose 20 pounds."
    return {
        f"{checked_item}_impacted": True,
        f"{checked_item}_message": new_message
    }

# Router for if permission was granted.
def confirm_permission(state, checked_item, log_title):
    if verbose_subagent_steps:
        print(f"---------Confirm the agent can create a new {log_title}---------")
    if not state[f"{checked_item}_impacted"]:
        return "permission_denied"
    return "permission_granted"

# State if the prerequisite isn't allowed to be requested.
def permission_denied(state, abort_message):
    if verbose_subagent_steps:
        print(f"---------Abort Workout Day Scheduling---------")
    abort(404, description=abort_message)
    return {}


# Confirm that the desired section should be impacted.
def confirm_impact(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Changing User Phase Component=========")
    if verbose_subagent_steps:
        print(f"---------Confirm that the User Phase Component is Impacted---------")
    if not state["phase_component_impacted"]:
        if verbose_subagent_steps:
            print(f"---------No Impact---------")
        return "no_impact"
    return "impact"

# Retrieve User's Availability.
def retrieve_availability(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Availability for Workout Day Scheduling---------")
    return {"user_availability": retrieve_availability_for_week()}

# Confirm that a currently active availability exists to attach the a schedule to.
def confirm_availability(state: AgentState):
    return confirm_prerequisites(state=state, key_to_check="user_availability", log_title="Availability")

# Request permission from user to execute the availability initialization.
def ask_for_availability_permission(state: AgentState):
    return ask_for_permission(state=state, checked_item="availability", log_title="Availability")

# Router for if permission was granted.
def confirm_availability_permission(state: AgentState):
    return confirm_permission(state=state, checked_item="availability", log_title="Availability")

# State if the Availability isn't allowed to be requested.
def availability_permission_denied(state: AgentState):
    return permission_denied(state=state, abort_message="No active weekday availability found.")

def availability_node(state: AgentState):
    print(f"\n=========Changing User Availability=========")
    if state["availability_impacted"]:
        availability_agent = create_availability_agent()
        result = availability_agent.invoke({
            "user_id": state["user_id"], 
            "user_input": state["user_input"], 
            "attempts": state["attempts"], 
            "availability_impacted": state["availability_impacted"], 
            "availability_message": state["availability_message"]
        })
    else:
        result = {
            "availability_impacted": False, 
            "availability_message": None, 
            "availability_formatted": None
        }
    return {
        "availability_impacted": result["availability_impacted"], 
        "availability_message": result["availability_message"], 
        "availability_formatted": result["availability_formatted"]
    }

# Retrieve parent item that will be used for the current schedule.
def retrieve_parent(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Current Microcycle---------")
    user_id = state["user_id"]
    user_microcycle = current_microcycle(user_id)
    return {"user_microcycle": user_microcycle}

# Confirm that a currently active parent exists to attach the a schedule to.
def confirm_parent(state: AgentState):
    return confirm_prerequisites(state=state, key_to_check="user_microcycle", log_title="Microcycle")

# Request permission from user to execute the parent initialization.
def ask_for_parent_permission(state: AgentState):
    return ask_for_permission(state=state, checked_item="microcycle", log_title="Microcycle")

# Router for if permission was granted.
def confirm_parent_permission(state: AgentState):
    return confirm_permission(state=state, checked_item="microcycle", log_title="Microcycle")

# State if the Macrocycle isn't allowed to be requested.
def parent_permission_denied(state: AgentState):
    return permission_denied(state=state, abort_message="No active microcycle found.")

# Retrieve necessary information for the schedule creation.
def retrieve_information(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Information for Workout Day Scheduling---------")
    user_microcycle = state["user_microcycle"]
    user_availability = state["user_availability"]
    microcycle_id = user_microcycle.id
    phase_id = user_microcycle.mesocycles.phase_id
    duration = user_microcycle.duration.days
    start_date = user_microcycle.start_date

    microcycle_weekdays, user_workdays = duration_to_weekdays(duration, start_date, microcycle_id)
    weekday_availability, number_of_available_weekdays, total_availability = retrieve_weekday_availability_information_from_availability(user_availability)

    return {
        "microcycle_id": microcycle_id,
        "phase_id": phase_id,
        "duration": duration,
        "start_date": start_date,
        "microcycle_weekdays": microcycle_weekdays,
        "user_workdays": user_workdays,
        "weekday_availability": weekday_availability,
        "number_of_available_weekdays": number_of_available_weekdays,
        "total_availability": total_availability
    }

# Delete the old items belonging to the parent.
def delete_old_children(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Delete old Workout Days---------")
    microcycle_id = state["microcycle_id"]
    db.session.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
    if verbose:
        print("Successfully deleted")
    return {}

# Executes the agent to create the phase component schedule for each workout in the current microcycle.
def perform_workout_day_selection(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Perform Workout Day Scheduling---------")
    phase_id = state["phase_id"]
    microcycle_weekdays = state["microcycle_weekdays"]
    weekday_availability = state["weekday_availability"]
    number_of_available_weekdays = state["number_of_available_weekdays"]
    total_availability = state["total_availability"]

    parameters=retrieve_pc_parameters(phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability)
    constraints={}

    result = phase_component_main(parameters, constraints)
    if verbose:
        print_long_output(result["formatted"])

    return {
        "agent_output": result["output"]
    }

# Convert output from the agent to SQL models.
def agent_output_to_sqlalchemy_model(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Convert schedule to SQLAlchemy models.---------")
    phase_components_output = state["agent_output"]
    user_workdays = state["user_workdays"]

    for phase_component in phase_components_output:
        # Create a new component entry.
        new_component = User_Workout_Components(
            phase_component_id = phase_component["phase_component_id"],
            bodypart_id = phase_component["bodypart_id"],
            duration = phase_component["duration_var"]
        )

        # Append the component to its corresponding workday.
        user_workdays[phase_component["workday_index"]].workout_components.append(new_component)

    db.session.add_all(user_workdays)
    db.session.commit()
    return {"sql_models": user_workdays}

# Print output.
def get_formatted_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Formatted Schedule for user---------")
    user_microcycle = state["user_microcycle"]

    user_workout_days = user_microcycle.workout_days
    if not user_workout_days:
        abort(404, description="No workout_days found for the microcycle.")

    user_workout_days_dict = [user_workout_day.to_dict() for user_workout_day in user_workout_days]

    pc_dict = get_all_items(Phase_Component_Library)
    bodypart_dict = get_all_items(Bodypart_Library)

    formatted_schedule = print_workout_days_schedule(pc_dict, bodypart_dict, user_workout_days_dict)
    if verbose_formatted_schedule:
        print(formatted_schedule)
    return {"phase_component_formatted": formatted_schedule}

# Node to declare that the sub agent has ended.
def end_node(state: AgentState):
    if verbose_agent_introductions:
        print(f"=========Ending User Phase Component=========\n")
    return {}

# Create main agent.
def create_main_agent_graph():
    workflow = StateGraph(AgentState)
    microcycle_agent = create_microcycle_agent()

    workflow.add_node("retrieve_availability", retrieve_availability)
    workflow.add_node("ask_for_availability_permission", ask_for_availability_permission)
    workflow.add_node("availability_permission_denied", availability_permission_denied)
    workflow.add_node("availability", availability_node)
    workflow.add_node("retrieve_parent", retrieve_parent)
    workflow.add_node("ask_for_parent_permission", ask_for_parent_permission)
    workflow.add_node("parent_permission_denied", parent_permission_denied)
    workflow.add_node("microcycle", microcycle_agent)
    workflow.add_node("retrieve_information", retrieve_information)
    workflow.add_node("delete_old_children", delete_old_children)
    workflow.add_node("perform_workout_day_selection", perform_workout_day_selection)
    workflow.add_node("agent_output_to_sqlalchemy_model", agent_output_to_sqlalchemy_model)
    workflow.add_node("get_formatted_list", get_formatted_list)
    workflow.add_node("end_node", end_node)

    workflow.add_conditional_edges(
        START,
        confirm_impact,
        {
            "no_impact": "end_node",
            "impact": "retrieve_availability"
        }
    )

    workflow.add_conditional_edges(
        "retrieve_availability",
        confirm_availability,
        {
            "no_parent": "ask_for_availability_permission",
            "parent": "retrieve_parent"
        }
    )

    workflow.add_conditional_edges(
        "ask_for_availability_permission",
        confirm_availability_permission,
        {
            "permission_denied": "availability_permission_denied",
            "permission_granted": "availability"
        }
    )
    workflow.add_edge("availability", "retrieve_availability")

    workflow.add_conditional_edges(
        "retrieve_parent",
        confirm_parent,
        {
            "no_parent": "ask_for_parent_permission",
            "parent": "retrieve_information"
        }
    )

    workflow.add_conditional_edges(
        "ask_for_parent_permission",
        confirm_parent_permission,
        {
            "permission_denied": "parent_permission_denied",
            "permission_granted": "microcycle"
        }
    )
    workflow.add_edge("microcycle", "retrieve_parent")

    workflow.add_edge("retrieve_information", "delete_old_children")
    workflow.add_edge("delete_old_children", "perform_workout_day_selection")
    workflow.add_edge("perform_workout_day_selection", "agent_output_to_sqlalchemy_model")
    workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
    workflow.add_edge("parent_permission_denied", "end_node")
    workflow.add_edge("availability_permission_denied", "end_node")
    workflow.add_edge("get_formatted_list", "end_node")
    workflow.add_edge("end_node", END)

    return workflow.compile()
