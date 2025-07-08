from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from flask import abort
from langgraph.graph import StateGraph, START, END
from app.main_agent.user_workout_days import create_microcycle_scheduler_agent


from app import db
from app.models import User_Workout_Exercises

from app.agents.exercises import exercises_main
from app.utils.common_table_queries import current_workout_day

from .actions import retrieve_pc_parameters

from app.main_agent.utils import print_workout_exercises_schedule

from app.utils.print_long_output import print_long_output
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Workout Exercises -----------------------------------------

class AgentState(MainAgentState):
    user_workout_day: any
    workout_day_id: int
    loading_system_id: int

    start_date: any
    agent_output: list
    sql_models: any

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
    if verbose_subagent_steps:
        print(f"---------Confirm there is an active Workout Day---------")
    if not state["user_workout_day"]:
        return "no_parent"
    return "parent"

# Request permission from user to execute the parent initialization.
def ask_for_permission(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Ask user if a new Workout Day can be made---------")
    return {
        "phase_component_impacted": True,
        "phase_component_message": "I would like to lose 20 pounds."
    }

# Router for if permission was granted.
def confirm_permission(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Confirm the agent can create a new Workout Day---------")
    if not state["phase_component_impacted"]:
        return "permission_denied"
    return "permission_granted"

# State if the Macrocycle isn't allowed to be requested.
def permission_denied(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Abort Workout Exercise Scheduling---------")
    abort(404, description="No active workout_day found.")
    return {}

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

    # Retrieve parameters.
    parameters = retrieve_pc_parameters(user_workout_day)
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

# Create main agent.
def create_main_agent_graph():
    workflow = StateGraph(AgentState)
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    workflow.add_node("retrieve_parent", retrieve_parent)
    workflow.add_node("ask_for_permission", ask_for_permission)
    workflow.add_node("permission_denied", permission_denied)
    workflow.add_node("phase_component", microcycle_scheduler_agent)
    workflow.add_node("retrieve_information", retrieve_information)
    workflow.add_node("delete_old_children", delete_old_children)
    workflow.add_node("perform_workout_exercise_selection", perform_workout_exercise_selection)
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
            "permission_granted": "phase_component"
        }
    )
    workflow.add_edge("phase_component", "retrieve_parent")

    workflow.add_edge("retrieve_information", "delete_old_children")
    workflow.add_edge("delete_old_children", "perform_workout_exercise_selection")
    workflow.add_edge("perform_workout_exercise_selection", "agent_output_to_sqlalchemy_model")
    workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
    workflow.add_edge("permission_denied", END)
    workflow.add_edge("get_formatted_list", END)

    return workflow.compile()
