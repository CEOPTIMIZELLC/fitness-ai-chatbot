from flask import abort
import copy

from logging_config import LogMainSubAgent

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app import db
from app.models import User_Exercises, User_Workout_Days
from app.utils.common_table_queries import current_workout_day
from app.utils.datetime_to_string import recursively_change_dict_timedeltas

from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.main_agent.base_sub_agents.utils import new_input_request

from .edit_goal_model import EditGoal
from .edit_prompts import workout_edit_system_prompt
from .schedule_printer import SchedulePrinter
from .list_printer import Main as list_printer_main

# ----------------------------------------- User Workout Completion -----------------------------------------

keys_to_remove = [
    # "id", 
    "workout_day_id", 
    "phase_component_id", 
    "exercise_id", 
    "bodypart_id", 
    "date", 
    "component_id", 

    "true_exercise_flag", 
    "working_duration", 
    "intensity", 
    "one_rep_max", 

    "strained_duration", 
    "strained_working_duration", 
    "base_strain", 
    "component_id", 
]

# Method to remove keys from the schedule that aren't useful for the LLM.
def remove_unnecessary_keys_from_workout_schedule(schedule_list):
    for exercise in schedule_list:
        # Add unit of measurementforrequired fields.
        exercise["seconds_per_exercise"] = f"{exercise["seconds_per_exercise"]} seconds"
        exercise["rest"] = f"{exercise["rest"]} seconds"
        exercise["weight"] = f"{exercise["weight"]} lbs"
        
        # Make flag a boolean.
        if exercise["true_exercise_flag"] == "True Exercise":
            exercise["true_exercise_flag"] = True
        else:
            exercise["true_exercise_flag"] = False

        # Remove all items not useful for the AI
        for key_to_remove in keys_to_remove:
            exercise.pop(key_to_remove, None)
        
        # if exercise["weight"] == 0 and exercise["intensity"] == 0 and exercise["one_rep_max"] == 0:
        #     exercise.pop("weight", None)
        #     exercise.pop("intensity", None)
        #     exercise.pop("one_rep_max", None)

    return schedule_list

# Method to get the list names and ids.
def get_ids_and_names(list_of_dicts):
    string_output = ", \n".join(
        f"{{{{'id': {e["id"]}, 'exercise_name': {e["exercise_name"]}}}}}"
        for e in list_of_dicts
    )
    return f"[{string_output}]"

# Method to format a dictionary element to a string.
def dict_to_string(dict_item):
    string_output = ", ".join(
        f"'{key}': '{value}'" 
        for key, value in dict_item.items()
    )
    return string_output

# Method to format the workout summary for the LLM.
def list_of_dicts_to_string(list_of_dicts):
    string_output = ", \n".join(
        f"{{{{{dict_to_string(list_item)}}}}}"
        for list_item in list_of_dicts
    )
    return f"[{string_output}]"

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

    # Create prompt to request schedule edits.
    def edit_prompt_creator(self, schedule_list_original):
        schedule_list = remove_unnecessary_keys_from_workout_schedule(schedule_list_original)
        allowed_list = get_ids_and_names(schedule_list)
        schedule_summary = list_of_dicts_to_string(schedule_list)
        edit_prompt = workout_edit_system_prompt(schedule_summary, allowed_list)
        return edit_prompt

    # Items extracted from the edit request.
    def goal_edits_parser(self, goal_edits=None):
        # Return an empty dictionary of edits if no edits were made.
        if not goal_edits:
            return {}
    
        goal_edits_dict={}
        
        # Convert goal edits to a dictionary format
        for goal_edit in goal_edits:
            goal_edit_information = {
                "remove": goal_edit.remove, 
                "reps": goal_edit.reps, 
                "sets": goal_edit.sets, 
                "rest": goal_edit.rest, 
                "weight": goal_edit.weight, 
            }

            goal_edits_dict[goal_edit.id] = goal_edit_information

        return goal_edits_dict

    # Retrieve entry for the edit.
    def compare_edits(self, original_schedule, altered_schedule):
        edits_to_be_applyed = {}
        for original_schedule_item in original_schedule:
            original_schedule_item_id = original_schedule_item["id"]
            altered_schedule_item = altered_schedule[original_schedule_item_id]

            common_keys = set(original_schedule_item.keys()) & set(altered_schedule_item.keys())

            # Include the item if it has been indicated to be removed.
            if altered_schedule_item["remove"]:
                edits_to_be_applyed[original_schedule_item_id] = altered_schedule[original_schedule_item_id]

            # Only include the item if any value has been changed from the original.
            elif any(original_schedule_item[key] != altered_schedule_item[key] for key in common_keys):
                edits_to_be_applyed[original_schedule_item_id] = altered_schedule[original_schedule_item_id]
        return edits_to_be_applyed

    # Items extracted from the edit request.
    def goal_edit_request_parser(self, goal_class, edits_to_be_applyed):
        return {
            "is_edited": True if edits_to_be_applyed else False,
            "edits": edits_to_be_applyed,
            "other_requests": goal_class.other_requests
        }

    # Request permission from user to execute the parent initialization.
    def ask_for_edits(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Ask user if Workout Performance is Accurate---------")
        # Get a copy of the current schedule and remove the items not useful for the AI.
        formatted_schedule_list = state["schedule_printed"]

        result = interrupt({
            "task": f"Is the proposed schedule for the current {self.parent_title} accurate to the work you performed?\n\n{formatted_schedule_list}"
        })
        user_input = result["user_input"]
        LogMainSubAgent.verbose(f"Extract the {self.parent_title} Goal the following message: {user_input}")

        # Retrieve the schedule and format it for the prompt.
        schedule_list = state["schedule_list"]
        edit_prompt = self.edit_prompt_creator(copy.deepcopy(schedule_list))

        # Retrieve the new input for the parent item.
        goal_class = new_input_request(user_input, edit_prompt, EditGoal)

        new_schedule = goal_class.schedule
        if new_schedule: 
            # Convert to dictionary form.
            goal_edits_dict = self.goal_edits_parser(new_schedule)

            # Refine and remove entries that weren't edited.
            edits_to_be_applyed = self.compare_edits(state["schedule_list"], goal_edits_dict)
        else: 
            edits_to_be_applyed = {}

        # Parse the structured output values to a dictionary.
        return self.goal_edit_request_parser(goal_class, edits_to_be_applyed)

    # Confirm that the desired section should be edited.
    def confirm_edits(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Confirm that the {self.sub_agent_title} is Edited---------")
        if state["is_edited"]:
        # if state["edits"]:
            LogMainSubAgent.agent_steps(f"\t---------Is Edited---------")
            return "is_edited"
        return "not_edited"

    # Perform the edits.
    def perform_edits(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Performing the Requested Edits for {self.sub_agent_title}---------")
        return {}

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
        workflow.add_node("perform_edits", self.perform_edits)
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

        workflow.add_edge("get_proposed_list", "format_proposed_list")
        workflow.add_edge("format_proposed_list", "ask_for_edits")


        workflow.add_conditional_edges(
            "ask_for_edits",
            self.confirm_edits,
            {
                "is_edited": "perform_edits",
                "not_edited": "perform_workout_completion"
            }
        )

        workflow.add_edge("perform_edits", "retrieve_parent")

        workflow.add_edge("perform_workout_completion", "get_formatted_list")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)