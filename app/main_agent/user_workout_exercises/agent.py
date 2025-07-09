from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from flask import abort
from langgraph.graph import StateGraph, START, END
from app.main_agent.user_workout_days import create_microcycle_scheduler_agent
from app.main_agent.user_weekdays_availability import create_availability_agent

from app import db
from app.models import User_Workout_Exercises

from app.agents.exercises import exercises_main
from app.utils.common_table_queries import current_workout_day

from .actions import retrieve_availability_for_day, retrieve_pc_parameters

from app.main_agent.utils import print_workout_exercises_schedule

from app.utils.print_long_output import print_long_output
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Workout Exercises -----------------------------------------

class AgentState(MainAgentState):
    user_workout_day: any
    workout_day_id: int
    loading_system_id: int

    user_availability: any
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
        print(f"---------Abort Workout Exercise Scheduling---------")
    abort(404, description=abort_message)
    return {}


# Confirm that the desired section should be impacted.
def confirm_impact(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Changing User Workout=========")
    if verbose_subagent_steps:
        print(f"---------Confirm that the User Workout is Impacted---------")
    if not state["workout_schedule_impacted"]:
        if verbose_subagent_steps:
            print(f"---------No Impact---------")
        return "no_impact"
    return "impact"

# Retrieve parent item that will be used for the current schedule.
def retrieve_parent(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Current Workout Day---------")
    user_id = state["user_id"]
    user_workout_day = current_workout_day(user_id)
    return {"user_workout_day": user_workout_day}

# Confirm that a currently active parent exists to attach the a schedule to.
def confirm_parent(state: AgentState):
    return confirm_prerequisites(state=state, key_to_check="user_workout_day", log_title="Workout Day")

# Request permission from user to execute the parent initialization.
def ask_for_parent_permission(state: AgentState):
    return ask_for_permission(state=state, checked_item="phase_component", log_title="Workout Day")

# Router for if permission was granted.
def confirm_parent_permission(state: AgentState):
    return confirm_permission(state=state, checked_item="phase_component", log_title="Workout Day")

# State if the Workout Phase Component isn't allowed to be requested.
def parent_permission_denied(state: AgentState):
    return permission_denied(state=state, abort_message="No active workout_day found.")


# Retrieve User's Availability.
def retrieve_availability(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Availability for Workout Scheduling---------")
    user_workout_day = state["user_workout_day"]
    return {"user_availability": retrieve_availability_for_day(user_workout_day)}

# Confirm that a currently active availability exists to attach the a schedule to.
def confirm_availability(state: AgentState):
    return confirm_prerequisites(state=state, key_to_check="user_availability", log_title="Availability")

# Request permission from user to execute the availability initialization.
def ask_for_availability_permission(state: AgentState):
    return ask_for_permission(state=state, checked_item="user_availability", log_title="Availability")

# Router for if permission was granted.
def confirm_availability_permission(state: AgentState):
    return confirm_permission(state=state, checked_item="user_availability", log_title="Availability")

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

# Retrieve necessary information for the schedule creation.
def retrieve_information(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Information for Workout Exercise Scheduling---------")
    user_workout_day = state["user_workout_day"]

    return {
        "workout_day_id": user_workout_day.id,
        "loading_system_id": user_workout_day.loading_systems.id
    }

# Delete the old items belonging to the parent.
def delete_old_children(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Delete old Workout Exercises---------")
    workout_day_id = state["workout_day_id"]
    db.session.query(User_Workout_Exercises).filter_by(workout_day_id=workout_day_id).delete()
    if verbose:
        print("Successfully deleted")
    return {}

# Executes the agent to create the phase component schedule for each workout in the current workout_day.
def perform_workout_exercise_selection(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Perform Workout Exercise Scheduling---------")
    user_workout_day = state["user_workout_day"]
    loading_system_id = state["loading_system_id"]

    availability = state["user_availability"]

    # Retrieve parameters.
    parameters = retrieve_pc_parameters(user_workout_day, availability)
    constraints={"vertical_loading": loading_system_id == 1}

    result = exercises_main(parameters, constraints)
    if verbose:
        print_long_output(result["formatted"])

    return {
        "agent_output": result["output"]
    }

# Convert output from the agent to SQL models.
def agent_output_to_sqlalchemy_model(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Convert schedule to SQLAlchemy models.---------")
    workout_day_id = state["workout_day_id"]
    exercises_output = state["agent_output"]

    user_workout_exercises = []
    for i, exercise in enumerate(exercises_output, start=1):
        # Create a new exercise entry.
        new_exercise = User_Workout_Exercises(
            workout_day_id = workout_day_id,
            phase_component_id = exercise["phase_component_id"],
            exercise_id = exercise["exercise_id"],
            bodypart_id = exercise["bodypart_id"],
            order = i,
            reps = exercise["reps_var"],
            sets = exercise["sets_var"],
            intensity = exercise["intensity_var"],
            rest = exercise["rest_var"],
            weight = exercise["training_weight"],
        )

        user_workout_exercises.append(new_exercise)

    db.session.add_all(user_workout_exercises)
    db.session.commit()
    return {"sql_models": user_workout_exercises}

# Print output.
def get_formatted_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Formatted Schedule for user---------")
    user_workout_day = state["user_workout_day"]

    user_workout_exercises = user_workout_day.exercises
    if not user_workout_exercises:
        abort(404, description="No exercises for the day found.")
    
    loading_system_id = state["loading_system_id"]

    user_workout_exercises_dict = [user_workout_exercise.to_dict() | 
                                {"component_id": user_workout_exercise.phase_components.components.id}
                                for user_workout_exercise in user_workout_exercises]
    
    formatted_schedule = print_workout_exercises_schedule(loading_system_id, user_workout_exercises_dict)
    if verbose_formatted_schedule:
        print_long_output(formatted_schedule)

    return {"workout_schedule_formatted": formatted_schedule}

# Node to declare that the sub agent has ended.
def end_node(state: AgentState):
    if verbose_agent_introductions:
        print(f"=========Ending User Workout=========\n")
    return {}

# Create main agent.
def create_main_agent_graph():
    workflow = StateGraph(AgentState)
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    workflow.add_node("retrieve_parent", retrieve_parent)
    workflow.add_node("ask_for_parent_permission", ask_for_parent_permission)
    workflow.add_node("parent_permission_denied", parent_permission_denied)
    workflow.add_node("phase_component", microcycle_scheduler_agent)
    workflow.add_node("retrieve_availability", retrieve_availability)
    workflow.add_node("ask_for_availability_permission", ask_for_availability_permission)
    workflow.add_node("availability_permission_denied", availability_permission_denied)
    workflow.add_node("availability", availability_node)
    workflow.add_node("retrieve_information", retrieve_information)
    workflow.add_node("delete_old_children", delete_old_children)
    workflow.add_node("perform_workout_exercise_selection", perform_workout_exercise_selection)
    workflow.add_node("agent_output_to_sqlalchemy_model", agent_output_to_sqlalchemy_model)
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
            "no_parent": "ask_for_parent_permission",
            "parent": "retrieve_availability"
        }
    )

    workflow.add_conditional_edges(
        "ask_for_parent_permission",
        confirm_parent_permission,
        {
            "permission_denied": "parent_permission_denied",
            "permission_granted": "phase_component"
        }
    )
    workflow.add_edge("phase_component", "retrieve_parent")

    workflow.add_conditional_edges(
        "retrieve_availability",
        confirm_availability,
        {
            "no_parent": "ask_for_availability_permission",
            "parent": "retrieve_information"
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
    workflow.add_edge("availability", "retrieve_parent")

    workflow.add_edge("retrieve_information", "delete_old_children")
    workflow.add_edge("delete_old_children", "perform_workout_exercise_selection")
    workflow.add_edge("perform_workout_exercise_selection", "agent_output_to_sqlalchemy_model")
    workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
    workflow.add_edge("parent_permission_denied", "end_node")
    workflow.add_edge("availability_permission_denied", "end_node")
    workflow.add_edge("get_formatted_list", "end_node")
    workflow.add_edge("end_node", END)

    return workflow.compile()
