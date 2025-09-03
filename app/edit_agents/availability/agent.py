from logging_config import LogEditorAgent

from app import db
from app.models import Weekday_Library

from app.schedule_printers import AvailabilitySchedulePrinter
from app.edit_agents.base import BaseSubAgent, TState

from .edit_goal_model import AvailabilityScheduleEditGoal
from .edit_prompt import AvailabilityEditPrompt
from .validity_check import check_schedule_validity

# ----------------------------------------- User Mesocycles -----------------------------------------

keys_to_remove = [
]

class SubAgent(BaseSubAgent, AvailabilityEditPrompt):
    edit_goal = AvailabilityScheduleEditGoal
    list_printer_class = AvailabilitySchedulePrinter()
    schedule_id_key = "weekday_id"
    schedule_name_key = "weekday_name"
    keys_to_remove = keys_to_remove

    # Format the fields of the workout schedule to improve performance from the LLM.
    def format_fields_for_schedule(self, schedule_item):
        # Add unit of measurement for required fields.
        schedule_item["id"] = schedule_item[self.schedule_id_key]
        schedule_item["availability"] = f"{schedule_item["availability"]} seconds"
        return schedule_item

    # Adds necessary keys for the formatter to the schedule item. 
    def add_necessary_keys_to_schedule_item(self, schedule_list):
        for schedule_item in schedule_list:
            weekday_entry = db.session.get(Weekday_Library, schedule_item["weekday_id"])
            schedule_item["weekday_name"] = weekday_entry.name
        return schedule_list

    # Retrieves the fields from the Pydantic model output.
    def edit_model_to_dict(self, goal_edit):
        return {
            self.schedule_id_key: goal_edit.id, 
            "availability": goal_edit.availability, 
        }

    # Specific code for extracting information from the edited schedule into the new one.
    def apply_edit_to_schedule_item(self, schedule_item, schedule_edit):
        schedule_item["availability"] = schedule_edit["availability"]
        return schedule_item

    # Check if the user's edits produce a valid schedule.
    def gather_schedule_violations(self, schedule_list):
        return check_schedule_validity(schedule_list)

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph()