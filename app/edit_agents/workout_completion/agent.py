from logging_config import LogEditorAgent

import copy
import math

# Database imports.
from app import db
from app.models import User_Workout_Exercises

# Agent construction imports.
from app.edit_agents.base.base import BaseSubAgent, AgentState
from app.schedule_printers.workout_completion import WorkoutCompletionListPrinter

# Local imports.
from .edit_goal_model import WorkoutCompletionEditGoal
from .edit_prompt import WorkoutCompletionEditPrompt

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

class WorkoutCompleteAgentState(AgentState):
    workout_day_id: int

class SubAgent(BaseSubAgent, WorkoutCompletionEditPrompt):
    edit_goal = WorkoutCompletionEditGoal
    list_printer_class = WorkoutCompletionListPrinter()
    schedule_id_key = "id"
    schedule_name_key = "exercise_name"
    keys_to_remove = keys_to_remove

    # Format the structured schedule.
    def _get_formatted_proposed_list(self, state, schedule_key, schedule_printed_key):
        schedule_list = state[schedule_key]

        # Add necessary keys for the formatter to the schedule items 
        schedule_list = self.add_necessary_keys_to_schedule_item(schedule_list)

        formatted_schedule = self.list_printer_class.run_printer(schedule_list)
        LogEditorAgent.formatted_schedule(formatted_schedule)

        return {
            schedule_key: schedule_list, 
            schedule_printed_key: formatted_schedule
        }

    # Format the fields of the workout schedule to improve performance from the LLM.
    def format_fields_for_schedule(self, schedule_item):
        return schedule_item

    # Adds necessary keys for the formatter to the schedule item. 
    def add_necessary_keys_to_schedule_item(self, schedule_list):
        for schedule_item in schedule_list:
            schedule_item["id"] = schedule_item[self.schedule_id_key]
        return schedule_list

    # Specific code for extracting information from the edited schedule into the new one.
    def apply_edit_to_schedule_item(self, schedule_item, schedule_edit, workout_day_id):
        # If there is a desire to remove the entry, remove it.
        if schedule_edit["remove"]:
            db.session.query(User_Workout_Exercises).filter_by(id=schedule_edit["id"], workout_day_id=workout_day_id).delete()
            return schedule_item

        schedule_entry = db.session.query(User_Workout_Exercises).filter_by(id=schedule_edit["id"], workout_day_id=workout_day_id).first()
        # Skip the item if it doesn't exist
        if not schedule_entry:
            return schedule_item

        new_sec_per_ex = schedule_item["seconds_per_exercise"]
        new_reps = schedule_edit["reps"]
        new_sets = schedule_edit["sets"]
        new_rest = schedule_edit["rest"]

        schedule_item["reps"] = new_reps
        schedule_entry.reps = new_reps
        schedule_item["sets"] = new_sets
        schedule_entry.sets = new_sets
        schedule_item["rest"] = new_rest
        schedule_entry.rest = new_rest

        # Calculate the new duration, working duration, density, and volume.
        schedule_item["duration"] = (new_sec_per_ex * new_reps + new_rest) * new_sets
        schedule_item["working_duration"] = (new_sec_per_ex * new_reps) * new_sets
        schedule_item["density"] = math.floor(100 * schedule_item["working_duration"] / schedule_item["duration"]) / 100
        schedule_item["volume"] = new_reps * new_sets

        # In case a weight is accidentally applied to a non-weighted exercises
        if schedule_item["weight"]:
            new_weight = int(schedule_item["weight"])
            new_one_rep_max = schedule_item["one_rep_max"]
            new_intensity = int(100 * schedule_item["weight"] / new_one_rep_max)

            schedule_item["weight"] = new_weight
            schedule_entry.weight = new_weight

            # Calculate new intensity.
            schedule_item["intensity"] = new_intensity
            schedule_entry.intensity = new_intensity

            # Factor in the new weight into the volume.
            schedule_item["volume"] *= schedule_item["weight"]

        # Calculate the new performance
        schedule_item["performance"] = math.floor(schedule_item["volume"] * schedule_item["density"] * 100) / 100
        db.session.commit()
        return schedule_item

    # Perform the edits.
    def perform_edits(self, state):
        LogEditorAgent.agent_steps(f"\t---------Performing the Requested Edits for the Schedule---------")

        workout_day_id = state["workout_day_id"]

        # Retrieve the schedule and format it for the prompt.
        schedule_list = copy.deepcopy(state["agent_output"])
        schedule_edits = state["edits"]

        # Apply the edits to the schedule.
        for schedule_item in schedule_list:
            schedule_item_id = schedule_item[self.schedule_id_key]

            # Skip the entry if the schedule item isn't present.
            if schedule_item_id not in schedule_edits.keys():
                continue

            schedule_edit = schedule_edits[schedule_item_id]

            self.apply_edit_to_schedule_item(schedule_item, schedule_edit, workout_day_id)
        
        return {"edited_schedule": schedule_list}

    # Check if the user's edits produce a valid schedule.
    def gather_schedule_violations(self, state):
        return []

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(WorkoutCompleteAgentState)