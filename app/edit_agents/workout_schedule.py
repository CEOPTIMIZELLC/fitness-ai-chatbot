from app.edit_goal_models import WorkoutScheduleEditGoal
from app.edit_prompts import WorkoutScheduleEditPrompt
from app.list_printers import WorkoutScheduleListPrinter
from .base import BaseSubAgent

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

class SubAgent(BaseSubAgent, WorkoutScheduleEditPrompt):
    edit_goal = WorkoutScheduleEditGoal
    list_printer_class = WorkoutScheduleListPrinter()
    schedule_id_key = "exercise_index"
    schedule_name_key = "exercise_name"
    keys_to_remove = keys_to_remove

    # Format the fields of the workout schedule to improve performance from the LLM.
    def format_fields_for_schedule(self, schedule_item):
        # Add unit of measurement for required fields.
        schedule_item["seconds_per_exercise"] = f"{schedule_item["seconds_per_exercise"]} seconds"
        schedule_item["reps"] = f"{schedule_item["reps"]} reps"
        schedule_item["sets"] = f"{schedule_item["sets"]} sets"
        schedule_item["rest"] = f"{schedule_item["rest"]} seconds"
        schedule_item["duration"] = f"{schedule_item["duration"]} seconds"
        schedule_item["weight"] = f"{schedule_item["weight"]} lbs"
        return schedule_item

    # Adds necessary keys for the formatter to the schedule item. 
    def add_necessary_keys_to_schedule_item(self, schedule_list):
        for schedule_item in schedule_list:
            schedule_item["id"] = schedule_item[self.schedule_id_key]
            schedule_item["phase_component_subcomponent"] = schedule_item["phase_component_name"]
            schedule_item["bodypart"] = schedule_item["bodypart_name"]
            schedule_item["is_warmup"] = schedule_item["warmup"]
        return schedule_list

    # Retrieves the fields from the Pydantic model output.
    def edit_model_to_dict(self, goal_edit):
        return {
            self.schedule_id_key: goal_edit.id, 
            "remove": goal_edit.remove, 
            "reps": goal_edit.reps, 
            "sets": goal_edit.sets, 
            "rest": goal_edit.rest, 
            "weight": goal_edit.weight, 
        }

    # Items extracted from the edit request.
    def goal_edit_request_parser(self, goal_class, edits_to_be_applyed):
        return {
            "is_edited": True if edits_to_be_applyed else False,
            "edits": edits_to_be_applyed,
            # "should_regenerate": goal_class.regenerate,
            "other_requests": goal_class.other_requests
        }

    # Specific code for extracting information from the edited schedule into the new one.
    def apply_edit_to_schedule_item(self, schedule_item, schedule_edit):
        schedule_item["reps"] = schedule_edit["reps"]
        schedule_item["sets"] = schedule_edit["sets"]
        schedule_item["rest"] = schedule_edit["rest"]

        # In case a weight is accidentally applied to a non-weighted exercises
        if schedule_item["weight"]:
            schedule_item["weight"] = schedule_edit["weight"]

            # Calculate new intensity.
            schedule_item["intensity"] = schedule_item["weight"] / schedule_item["one_rep_max"]
        return schedule_item

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph()