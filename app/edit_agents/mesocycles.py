from app.edit_goal_models import MesocycleScheduleEditGoal
from app.edit_prompts import MesocycleEditPrompt
from app.schedule_printers import MesocycleSchedulePrinter
from .base import BaseSubAgent

# ----------------------------------------- User Mesocycles -----------------------------------------

keys_to_remove = [
    "name", 
    "order"
]

class SubAgent(BaseSubAgent, MesocycleEditPrompt):
    edit_goal = MesocycleScheduleEditGoal
    list_printer_class = MesocycleSchedulePrinter()
    schedule_id_key = "order"
    schedule_name_key = "phase_name"
    keys_to_remove = keys_to_remove

    # Format the fields of the workout schedule to improve performance from the LLM.
    def format_fields_for_schedule(self, schedule_item):
        # Add unit of measurement for required fields.
        schedule_item["id"] = schedule_item[self.schedule_id_key]
        schedule_item["start_date"] = str(schedule_item["start_date"])
        schedule_item["end_date"] = str(schedule_item["end_date"])
        schedule_item["duration"] = f"{schedule_item["duration"]} weeks"
        return schedule_item

    # Adds necessary keys for the formatter to the schedule item. 
    def add_necessary_keys_to_schedule_item(self, schedule_list):
        for schedule_item in schedule_list:
            schedule_item["phase_name"] = schedule_item["name"]
        return schedule_list

    # Retrieves the fields from the Pydantic model output.
    def edit_model_to_dict(self, goal_edit):
        return {
            self.schedule_id_key: goal_edit.id, 
            "remove": goal_edit.remove, 
            "start_date": goal_edit.start_date, 
            "end_date": goal_edit.end_date, 
        }

    # Specific code for extracting information from the edited schedule into the new one.
    def apply_edit_to_schedule_item(self, schedule_item, schedule_edit):
        schedule_item["start_date"] = schedule_edit["start_date"]
        schedule_item["end_date"] = schedule_edit["end_date"]
        schedule_item["duration"] = (schedule_edit["end_date"] - schedule_edit["start_date"]).days // 7
        return schedule_item

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph()