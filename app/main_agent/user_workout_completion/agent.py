from flask import abort
import copy

from logging_config import LogMainSubAgent

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app import db
from app.models import User_Exercises, User_Workout_Days
from app.utils.common_table_queries import current_workout_day
from app.utils.datetime_to_string import recursively_change_dict_timedeltas

from app.main_agent.edit_prompts import workout_edit_system_prompt
from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.main_agent.base_sub_agents.utils import new_input_request

from .edit_goal_model import EditGoal
from .schedule_printer import SchedulePrinter
from .list_printer import Main as list_printer_main

# ----------------------------------------- User Workout Completion -----------------------------------------

keys_to_remove = [
    "id", 
    "workout_day_id", 
    "phase_component_id", 
    "exercise_id", 
    "bodypart_id", 
    "date", 
    "component_id", 
    "strained_duration", 
    "strained_working_duration", 
    "component_id", 
    "component_id", 
]

class AgentState(MainAgentState):
    user_workout_day: dict
    workout_exercises: list
    user_exercises: list
    old_user_exercises: list
    schedule_list: list
    schedule_printed: str

class SubAgent(BaseAgent, SchedulePrinter):
    focus = "workout_completion"
    parent = "workout_day"
    sub_agent_title = "Workout Completion"
    parent_title = "Workout Day"
    edit_prompt = workout_edit_system_prompt

    # def focus_retriever_agent(self, user_id):
    #     return current_workout_day(user_id)

    def parent_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for {self.sub_agent_title}---------")
        user_workout_day = state[self.parent_names["entry"]]
        workout_exercises = user_workout_day["exercises"]

        return {"workout_exercises": workout_exercises}

    # Confirm that there is a workout to complete.
    def confirm_children(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active Workout---------")
        if not state["workout_exercises"]:
            return "no_schedule"
        return "present_schedule"

    # Create the structured schedule.
    def get_proposed_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Get Proposed Workout Schedule---------")
        user_workout_day = state[self.parent_names["entry"]]
        workout_day_id = user_workout_day["id"]
        parent_db_entry = db.session.get(User_Workout_Days, workout_day_id)

        schedule_from_db = parent_db_entry.exercises
        if not schedule_from_db:
            abort(404, description=f"No exercises found for the workout.")

        user_workout_exercises_dict = [user_workout_exercise.to_dict() | 
                                    {"component_id": user_workout_exercise.phase_components.components.id}
                                    for user_workout_exercise in schedule_from_db]

        schedule_list = recursively_change_dict_timedeltas(user_workout_exercises_dict)

        return {"schedule_list": schedule_list}

    # Format the structured schedule.
    def format_proposed_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Format Proposed Workout Schedule---------")
        schedule_list = state["schedule_list"]

        formatted_schedule = list_printer_main(schedule_list)
        LogMainSubAgent.formatted_schedule(formatted_schedule)

        return {"schedule_printed": formatted_schedule}

    # Request permission from user to execute the parent initialization.
    def ask_for_edits(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Ask user if Workout Performance is Accurate---------")
        # Get a copy of the current schedule and remove the items not useful for the AI.
        schedule_list = copy.deepcopy(state["schedule_list"])
        for exercise in schedule_list:
            # Remove all items not useful for the AI
            for key_to_remove in keys_to_remove:
                exercise.pop(key_to_remove, None)

        import json
        print(json.dumps(schedule_list, indent=4))

        result = interrupt({
            "task": f"Is the proposed schedule for the current {self.parent_title} accurate to the work you performed?"
        })
        user_input = result["user_input"]
        LogMainSubAgent.verbose(f"Extract the {self.parent_title} Goal the following message: {user_input}")

        # Retrieve the new input for the parent item.
        goal_class = new_input_request(user_input, self.edit_prompt, EditGoal)

        # Parse the structured output values to a dictionary.
        return self.goal_classifier_parser(self.parent_names, goal_class)

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

            # db.session.commit()

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

        formatted_schedule = self.run_schedule_printer(old_user_exercises, user_exercises)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)

        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("get_proposed_list", self.get_proposed_list)
        workflow.add_node("format_proposed_list", self.format_proposed_list)
        workflow.add_node("ask_for_edits", self.ask_for_edits)
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
                "present_schedule": "get_proposed_list"
            }
        )

        workflow.add_edge("format_proposed_list", "format_proposed_list")
        workflow.add_edge("get_proposed_list", "ask_for_edits")
        workflow.add_edge("ask_for_edits", "perform_workout_completion")
        workflow.add_edge("perform_workout_completion", "get_formatted_list")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)