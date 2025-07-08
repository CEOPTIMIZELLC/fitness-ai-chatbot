from config import verbose, verbose_formatted_schedule, verbose_agent_introductions
from flask import abort
from flask_login import current_user
from datetime import timedelta
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END


from app import db
from app.models import User_Workout_Components, User_Workout_Days, User_Microcycles, Bodypart_Library, Phase_Component_Library

from app.agents.phase_components import Main as phase_component_main
from app.utils.common_table_queries import current_microcycle, current_workout_day

from .actions import duration_to_weekdays, retrieve_availability, retrieve_weekday_availability_information_from_availability, retrieve_pc_parameters

from app.main_agent.utils import construct_phases_list
from app.main_agent.utils import print_workout_days_schedule

from app.utils.print_long_output import print_long_output
from app.utils.db_helpers import get_all_items
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Workout_Days -----------------------------------------

microcycle_weeks = 26

class AgentState(MainAgentState):
    user_microcycle: any
    microcycle_id: int
    phase_id: int
    duration: any

    microcycle_weekdays: list
    user_workdays: list

    weekday_availability: list
    number_of_available_weekdays: int
    total_availability: int

    start_date: any
    agent_output: list
    sql_models: any

def retrieve_parent(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Changing User Phase Component=========")
    print(f"---------Retrieving Current Microcycle---------")
    user_id = state["user_id"]
    user_microcycle = current_microcycle(user_id)

    # if not user_microcycle:
    #     abort(404, description="No active microcycle found.")

    return {"user_microcycle": user_microcycle}

def confirm_parent(state: AgentState):
    print(f"---------Confirm there is an active Microcycle---------")
    if not state["user_microcycle"]:
        return "no_parent"
    return "parent"

def ask_for_permission(state: AgentState):
    print(f"---------Ask user if a new Microcycle can be made---------")
    abort(404, description="No active microcycle found.")
    return {}

def retrieve_information(state: AgentState):
    print(f"---------Retrieving Information for Workout_Day Scheduling---------")
    user_microcycle = state["user_microcycle"]
    microcycle_id = user_microcycle.id
    phase_id = user_microcycle.mesocycles.phase_id
    duration = user_microcycle.duration.days
    start_date = user_microcycle.start_date

    availability = retrieve_availability()
    microcycle_weekdays, user_workdays = duration_to_weekdays(duration, start_date, microcycle_id)
    weekday_availability, number_of_available_weekdays, total_availability = retrieve_weekday_availability_information_from_availability(availability)

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

def delete_old_children(state: AgentState):
    print(f"---------Delete old Workout_Days---------")
    microcycle_id = state["microcycle_id"]
    db.session.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
    if verbose:
        print("Successfully deleted")
    return {}

def perform_workout_day_selection(state: AgentState):
    print(f"---------Perform Workout_Day Scheduling---------")
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

def agent_output_to_sqlalchemy_model(state: AgentState):
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

def get_formatted_list(state: AgentState):
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

def create_main_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve_parent", retrieve_parent)
    workflow.add_node("ask_for_permission", ask_for_permission)
    workflow.add_node("retrieve_information", retrieve_information)
    workflow.add_node("delete_old_children", delete_old_children)
    workflow.add_node("perform_workout_day_selection", perform_workout_day_selection)
    workflow.add_node("agent_output_to_sqlalchemy_model", agent_output_to_sqlalchemy_model)
    workflow.add_node("get_formatted_list", get_formatted_list)

    workflow.add_conditional_edges(
        "retrieve_parent",
        confirm_parent,
        {
            "no_parent": "ask_for_permission",
            "parent": "retrieve_information"
        }
    )

    workflow.add_edge("retrieve_information", "delete_old_children")
    workflow.add_edge("delete_old_children", "perform_workout_day_selection")
    workflow.add_edge("perform_workout_day_selection", "agent_output_to_sqlalchemy_model")
    workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
    workflow.add_edge("ask_for_permission", END)
    workflow.add_edge("get_formatted_list", END)

    workflow.set_entry_point("retrieve_parent")

    return workflow.compile()
