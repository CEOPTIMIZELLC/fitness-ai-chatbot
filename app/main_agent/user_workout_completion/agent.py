from flask import abort

from logging_config import LogMainSubAgent

from langgraph.graph import StateGraph, START, END

from app import db
from app.models import User_Exercises, User_Workout_Days
from app.utils.common_table_queries import current_workout_day

from app.main_agent.main_agent_state import MainAgentState

from .schedule_printer import Main as print_schedule
from .list_printer import Main as list_printer_main

# ----------------------------------------- User Workout Completion -----------------------------------------

class AgentState(MainAgentState):
    user_workout_day: dict
    workout_exercises: list
    user_exercises: list
    old_user_exercises: list
    schedule_list: list
    schedule_printed: str

class SubAgent:
    sub_agent_title = "Workout Completion"
    parent_title = "Workout Day"

    # Confirm that the desired section should be impacted.
    def confirm_impact(self, state: AgentState):
        LogMainSubAgent.agent_introductions(f"\n=========Starting User {self.sub_agent_title}=========")
        LogMainSubAgent.agent_steps(f"\t---------Confirm that the User Microcycle is Impacted---------")
        if not state["workout_completion_impacted"]:
            LogMainSubAgent.agent_steps(f"\t---------No Impact---------")
            return "no_impact"
        return "impact"

    # Retrieve parent item that will be used for the current schedule.
    def retrieve_parent(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Current {self.parent_title}---------")
        user_id = state["user_id"]
        user_workout_day = current_workout_day(user_id)

        # Return parent.
        return {"user_workout_day": user_workout_day.to_dict() if user_workout_day else None}

    # Confirm that a currently active parent exists to attach the a schedule to.
    def confirm_parent(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active {self.parent_title}---------")
        if not state["user_workout_day"]:
            return "no_parent"
        return "parent"

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for {self.sub_agent_title}---------")
        user_workout_day = state["user_workout_day"]
        workout_exercises = user_workout_day["exercises"]

        return {"workout_exercises": workout_exercises}

    # Confirm that there is a workout to complete.
    def confirm_children(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active Workout---------")
        if not state["workout_exercises"]:
            return "no_schedule"
        return "present_schedule"

    # Print output.
    def get_user_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Show Proposed Workout Schedule---------")
        user_workout_day = state["user_workout_day"]
        workout_day_id = user_workout_day["id"]
        parent_db_entry = db.session.get(User_Workout_Days, workout_day_id)

        schedule_from_db = parent_db_entry.exercises
        if not schedule_from_db:
            abort(404, description=f"No exercises found for the workout.")

        user_workout_exercises_dict = [user_workout_exercise.to_dict() | 
                                    {"component_id": user_workout_exercise.phase_components.components.id}
                                    for user_workout_exercise in schedule_from_db]

        formatted_schedule = list_printer_main(user_workout_exercises_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {"schedule_printed": formatted_schedule}

    # Initializes the microcycle schedule for the current mesocycle.
    def perform_workout_completion(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Perform {self.sub_agent_title}---------")
        user_id = state["user_id"]
        workout_exercises = state["workout_exercises"]

        user_exercises = []
        old_user_exercises = []
        for exercise in workout_exercises:
            # Retrieve corresponding user exercise entry.
            user_exercise = db.session.get(
                User_Exercises, {
                    "user_id": user_id, 
                    "exercise_id": exercise["exercise_id"]})

            # Append old exercise performance for formatted schedule later.
            old_user_exercises.append(user_exercise.to_dict())

            # Only replace if the new one rep max is larger.
            user_exercise.one_rep_max = max(user_exercise.one_rep_max_decayed, exercise["one_rep_max"])
            user_exercise.one_rep_load = exercise["one_rep_max"]
            user_exercise.volume = exercise["volume"]
            user_exercise.density = exercise["density"]
            user_exercise.intensity = exercise["intensity"]
            user_exercise.duration = exercise["duration"]
            user_exercise.working_duration = exercise["working_duration"]
            user_exercise.last_performed = exercise["date"]

            # Only replace if the new performance is larger.
            user_exercise.performance = max(user_exercise.performance_decayed, exercise["performance"])

            db.session.commit()

            # Append new exercise performance for formatted schedule later.
            user_exercises.append(user_exercise.to_dict())

        return {
            "user_exercises": user_exercises, 
            "old_user_exercises": old_user_exercises
        }

    # Print output.
    def get_formatted_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_exercises = state["user_exercises"]
        old_user_exercises = state["old_user_exercises"]

        formatted_schedule = print_schedule(old_user_exercises, user_exercises)
        LogMainSubAgent.formatted_schedule(formatted_schedule)

        return {"workout_completion_formatted": formatted_schedule}

    # Node to declare that the sub agent has ended.
    def end_node(self, state: AgentState):
        LogMainSubAgent.agent_introductions(f"=========Ending User {self.sub_agent_title}=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)

        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("perform_workout_completion", self.perform_workout_completion)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("end_node", self.end_node)

        workflow.add_conditional_edges(
            START,
            self.confirm_impact,
            {
                "no_impact": "end_node",
                "impact": "retrieve_parent"
            }
        )

        workflow.add_conditional_edges(
            "retrieve_parent",
            self.confirm_parent,
            {
                "no_parent": "end_node",
                "parent": "retrieve_information"
            }
        )

        workflow.add_conditional_edges(
            "retrieve_information",
            self.confirm_children,
            {
                "no_schedule": "end_node",
                "present_schedule": "get_user_list"
            }
        )

        workflow.add_edge("get_user_list", "perform_workout_completion")
        workflow.add_edge("perform_workout_completion", "get_formatted_list")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)