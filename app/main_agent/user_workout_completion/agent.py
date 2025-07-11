from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from langgraph.graph import StateGraph, START, END

from app import db
from app.models import User_Exercises

from app.main_agent.utils import print_workout_exercises_completion

from app.utils.common_table_queries import current_workout_day
from app.utils.print_long_output import print_long_output
from app.main_agent.main_agent_state import MainAgentState

# ----------------------------------------- User Workout Completion -----------------------------------------

class AgentState(MainAgentState):
    user_workout_day: any
    workout_exercises: any
    user_exercises: any
    old_user_exercises: any

# Confirm that the desired section should be impacted.
def confirm_impact(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Changing User Workout Completion=========")
    if verbose_subagent_steps:
        print(f"\t---------Confirm that the User Microcycle is Impacted---------")
    if not state["workout_completion_impacted"]:
        if verbose_subagent_steps:
            print(f"\t---------No Impact---------")
        return "no_impact"
    return "impact"

# Retrieve parent item that will be used for the current schedule.
def retrieve_parent(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving Current Workout Day---------")
    user_id = state["user_id"]
    user_workout_day = current_workout_day(user_id)
    return {"user_workout_day": user_workout_day}

# Confirm that a currently active parent exists to attach the a schedule to.
def confirm_parent(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Confirm there is an active Workout Day---------")
    if not state["user_workout_day"]:
        return "no_parent"
    return "parent"

# Retrieve necessary information for the schedule creation.
def retrieve_information(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving Information for Microcycle Scheduling---------")
    user_id = state["user_id"]
    user_workout_day = state["user_workout_day"]
    workout_exercises = user_workout_day.exercises

    user_exercises = []
    for exercise in workout_exercises:
        user_exercise = db.session.get(User_Exercises, {
            "user_id": user_id, 
            "exercise_id": exercise.exercise_id})
        user_exercises.append(user_exercise)
    return {
        "workout_exercises": workout_exercises, 
        "user_exercises": user_exercises
    }

# Confirm that there is a workout to complete.
def confirm_children(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Confirm there is an active Workout---------")
    if not state["user_exercises"]:
        return "no_schedule"
    return "present_schedule"

# Initializes the microcycle schedule for the current mesocycle.
def perform_workout_completion(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Perform Workout Completion---------")
    workout_exercises = state["workout_exercises"]
    user_exercises = state["user_exercises"]

    old_user_exercises = []
    for exercise, user_exercise in zip(workout_exercises, user_exercises):
        # Append old exercise performance for formatted schedule later.
        old_user_exercises.append(user_exercise.to_dict())
        new_weight = exercise.weight or 0

        new_one_rep_max = round((new_weight * (30 + exercise.reps)) / 30, 2)

        # Only replace if the new one rep max is larger.
        user_exercise.one_rep_max = max(user_exercise.one_rep_max_decayed, new_one_rep_max)
        user_exercise.one_rep_load = new_one_rep_max
        user_exercise.volume = exercise.volume
        user_exercise.density = exercise.density
        user_exercise.intensity = exercise.intensity
        user_exercise.duration = exercise.duration
        user_exercise.working_duration = exercise.working_duration
        user_exercise.last_performed = exercise.workout_days.date

        # Only replace if the new performance is larger.
        user_exercise.performance = max(user_exercise.performance_decayed, exercise.performance)

        db.session.commit()
    return {"old_user_exercises": old_user_exercises}

# Print output.
def get_formatted_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"\t---------Retrieving Formatted Schedule for user---------")
    user_exercises = state["user_exercises"]
    old_user_exercises_dict = state["old_user_exercises"]

    user_exercises_dict = [user_exercise.to_dict() for user_exercise in user_exercises]
    
    formatted_schedule = print_workout_exercises_completion(user_exercises_dict, old_user_exercises_dict)
    if verbose_formatted_schedule:
        print_long_output(formatted_schedule)

    return {"workout_completion_formatted": formatted_schedule}

# Node to declare that the sub agent has ended.
def end_node(state: AgentState):
    if verbose_agent_introductions:
        print(f"=========Ending User Workout Completion=========\n")
    return {}

# Create main agent.
def create_main_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve_parent", retrieve_parent)
    workflow.add_node("retrieve_information", retrieve_information)
    workflow.add_node("perform_workout_completion", perform_workout_completion)
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
            "no_parent": "end_node",
            "parent": "retrieve_information"
        }
    )

    workflow.add_conditional_edges(
        "retrieve_information",
        confirm_children,
        {
            "no_schedule": "end_node",
            "present_schedule": "perform_workout_completion"
        }
    )

    workflow.add_edge("perform_workout_completion", "get_formatted_list")
    workflow.add_edge("get_formatted_list", "end_node")
    workflow.add_edge("end_node", END)

    return workflow.compile()
