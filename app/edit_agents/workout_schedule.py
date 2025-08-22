from config import request_schedule_edits
from logging_config import LogMainSubAgent
from flask import abort
import copy

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app.main_agent.base_sub_agents.utils import new_input_request
from app.edit_goal_models import WorkoutScheduleEditGoal
from app.edit_prompts import WorkoutScheduleEditPrompt
from app.list_printers import WorkoutScheduleListPrinter
from app.schedule_printers import WorkoutScheduleSchedulePrinter

# ----------------------------------------- User Workout Exercises -----------------------------------------

keys_to_remove = [
    # "id", 
    "workout_day_id", 
    "phase_component_id", 
    "bodypart_id", 
    "exercise_id", 
    "exercise_index", 
    "date", 
    "phase_component_index", 

    "phase_component_name", 
    "bodypart_name", 

    "volume", 
    "performance", 
    "density", 

    "true_exercise_flag", 
    "is_warmup", 
    "working_duration", 
    "intensity", 
    "one_rep_max", 

    "strained_duration", 
    "strained_working_duration", 
    "base_strain", 
    "component_id", 
    "warmup", 
    "i", 
]

class ScheduleFormatterMethods:
    # Method to remove keys from the schedule that aren't useful for the LLM.
    def remove_unnecessary_keys_from_workout_schedule(self, schedule_list):
        for exercise in schedule_list:
            # Add unit of measurementforrequired fields.
            exercise["seconds_per_exercise"] = f"{exercise["seconds_per_exercise"]} seconds"
            exercise["reps"] = f"{exercise["reps"]} reps"
            exercise["sets"] = f"{exercise["sets"]} sets"
            exercise["rest"] = f"{exercise["rest"]} seconds"
            exercise["duration"] = f"{exercise["duration"]} seconds"
            exercise["weight"] = f"{exercise["weight"]} lbs"

            # Remove all items not useful for the AI
            for key_to_remove in keys_to_remove:
                exercise.pop(key_to_remove, None)
        return schedule_list

    # Method to get the list names and ids.
    def get_ids_and_names(self, list_of_dicts):
        string_output = ", \n".join(
            f"{{{{'id': {e["exercise_index"]}, 'exercise_name': {e["exercise_name"]}}}}}"
            for e in list_of_dicts
        )
        return f"[{string_output}]"

    # Method to format a dictionary element to a string.
    def dict_to_string(self, dict_item):
        string_output = ", ".join(
            f"'{key}': '{value}'" 
            for key, value in dict_item.items()
            if key != "id"
        )
        return f"'id': {dict_item["id"]}, {string_output}"

    # Method to format the workout summary for the LLM.
    def list_of_dicts_to_string(self, list_of_dicts):
        string_output = ", \n".join(
            f"{{{{{self.dict_to_string(list_item)}}}}}"
            for list_item in list_of_dicts
        )
        return f"[{string_output}]"


# Confirm that the desired section should be edited.
def confirm_edits(state):
    LogMainSubAgent.agent_steps(f"\t---------Confirm that the Schedule is Edited---------")
    if state["is_edited"]:
    # if state["edits"]:
        LogMainSubAgent.agent_steps(f"\t---------Is Edited---------")
        return "is_edited"
    return "not_edited"

class AgentState(TypedDict):
    is_edited: bool
    edits: any
    other_requests: str
    agent_output: list
    schedule_printed: str


class SubAgent(ScheduleFormatterMethods, WorkoutScheduleEditPrompt):
    edit_goal = WorkoutScheduleEditGoal
    schedule_printer_class = WorkoutScheduleSchedulePrinter()
    list_printer_class = WorkoutScheduleListPrinter()

    # Format the structured schedule.
    def format_proposed_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Format Proposed Workout Schedule---------")
        schedule_list = state["agent_output"]

        for schedule_item in schedule_list:
            schedule_item["id"] = schedule_item["exercise_index"]
            schedule_item["phase_component_subcomponent"] = schedule_item["phase_component_name"]
            schedule_item["bodypart"] = schedule_item["bodypart_name"]
            schedule_item["is_warmup"] = schedule_item["warmup"]

        formatted_schedule = self.list_printer_class.run_list_printer(schedule_list)
        LogMainSubAgent.formatted_schedule(formatted_schedule)

        return {"schedule_printed": formatted_schedule}

    # Create prompt to request schedule edits.
    def edit_prompt_creator(self, schedule_list_original):
        allowed_list = self.get_ids_and_names(schedule_list_original)
        schedule_list = self.remove_unnecessary_keys_from_workout_schedule(schedule_list_original)
        schedule_summary = self.list_of_dicts_to_string(schedule_list)
        edit_prompt = self.edit_system_prompt_constructor(schedule_summary, allowed_list)
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
                "exercise_index": goal_edit.id, 
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
            original_schedule_item_id = original_schedule_item["exercise_index"]

            # Skip the entry if the schedule item isn't present.
            if original_schedule_item_id not in altered_schedule.keys():
                continue

            altered_schedule_item = altered_schedule[original_schedule_item_id]

            common_keys = set(original_schedule_item.keys()) & set(altered_schedule_item.keys())

            # Include the item if it has been indicated to be removed.
            if altered_schedule_item["remove"]:
                edits_to_be_applyed[original_schedule_item_id] = altered_schedule_item

            # Only include the item if any value has been changed from the original.
            elif any(original_schedule_item[key] != altered_schedule_item[key] for key in common_keys):
                edits_to_be_applyed[original_schedule_item_id] = altered_schedule_item
        return edits_to_be_applyed

    # Items extracted from the edit request.
    def goal_edit_request_parser(self, goal_class, edits_to_be_applyed):
        return {
            "is_edited": True if edits_to_be_applyed else False,
            "edits": edits_to_be_applyed,
            # "should_regenerate": goal_class.regenerate,
            "other_requests": goal_class.other_requests
        }

    # Request permission from user to execute the parent initialization.
    def ask_for_edits(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Ask user if edits should be made to the schedule---------")
        if not request_schedule_edits:
            LogMainSubAgent.agent_steps(f"\t---------Agent settings do not request edits.---------")
            return {
                "is_edited": False,
                "edits": {},
                # "should_regenerate": False,
                "other_requests": None
            }
        # Get a copy of the current schedule and remove the items not useful for the AI.
        formatted_schedule_list = state["schedule_printed"]

        result = interrupt({
            "task": f"Are there any edits you would like to make to the schedule?\n\n{formatted_schedule_list}"
        })
        user_input = result["user_input"]
        LogMainSubAgent.verbose(f"Extract the Edits from the following message: {user_input}")

        # Retrieve the schedule and format it for the prompt.
        schedule_list = state["agent_output"]
        edit_prompt = self.edit_prompt_creator(copy.deepcopy(schedule_list))

        # Retrieve the new input for the parent item.
        goal_class = new_input_request(user_input, edit_prompt, self.edit_goal)

        new_schedule = goal_class.schedule
        if new_schedule: 
            # Convert to dictionary form.
            goal_edits_dict = self.goal_edits_parser(new_schedule)

            # Refine and remove entries that weren't edited.
            edits_to_be_applyed = self.compare_edits(state["agent_output"], goal_edits_dict)
        else: 
            edits_to_be_applyed = {}

        return self.goal_edit_request_parser(goal_class, edits_to_be_applyed)

    # Perform the edits.
    def perform_edits(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Performing the Requested Edits for the Schedule---------")

        # Retrieve the schedule and format it for the prompt.
        schedule_list = state["agent_output"]
        schedule_edits = state["edits"]

        # Apply the schedule edits to the workout exercises.
        for schedule_item in schedule_list:
            # Skip the entry if the schedule item isn't present.
            if schedule_item["exercise_index"] not in schedule_edits.keys():
                continue

            schedule_edit = schedule_edits[schedule_item["exercise_index"]]

            schedule_item["reps"] = schedule_edit["reps"]
            schedule_item["sets"] = schedule_edit["sets"]
            schedule_item["rest"] = schedule_edit["rest"]

            # In case a weight is accidentally applied to a non-weighted exercises
            if schedule_item["weight"]:
                schedule_item["weight"] = schedule_edit["weight"]

                # Calculate new intensity.
                schedule_item["intensity"] = schedule_item["weight"] / schedule_item["one_rep_max"]
        
        return {"agent_output": schedule_list}

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogMainSubAgent.agent_introductions(f"=========Ending Editor SubAgent=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("format_proposed_list", self.format_proposed_list)
        workflow.add_node("ask_for_edits", self.ask_for_edits)
        workflow.add_node("perform_edits", self.perform_edits)
        workflow.add_node("end_node", self.end_node)

        # Create a formatted list for the user to review.
        workflow.add_edge(START, "format_proposed_list")
        workflow.add_edge("format_proposed_list", "ask_for_edits")

        # Whether any edits have been applied.
        workflow.add_conditional_edges(
            "ask_for_edits",
            confirm_edits,
            {
                "is_edited": "perform_edits",                           # The agent should apply the desired edits to the schedule.
                "not_edited": "end_node"                                # The agent should end if no edits were found.
            }
        )
        workflow.add_edge("perform_edits", "format_proposed_list")

        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph()