from logging_config import LogAlteringAgent
from flask import abort
from .utils import retrieve_current_agent_focus, sub_agent_focused_items

# ----------------------------------------- Base Sub Agent For Schedule Items -----------------------------------------

# Determine whether the schedule should be regenerated.
def confirm_regenerate(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogAlteringAgent.agent_steps(f"\t---------Determine if the {sub_agent_focus} schedule should be regenerated---------")
    if state.get("is_regenerated", False):
        LogAlteringAgent.agent_steps(f"\t---------Is Regenerated---------")
        return "is_regenerated"
    return "not_regenerated"

class BaseAgent():
    focus = ""
    sub_agent_title = ""
    focus_edit_agent = None
    is_edited = False
    schedule_printer_class = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)

    def focus_list_retriever_agent(self, user_id):
        pass

    # In between node for chained conditional edges.
    def chained_conditional_inbetween(self, state):
        return {}
    
    # Node to declare that the sub agent has begun.
    def start_node(self, state):
        LogAlteringAgent.agent_introductions(f"\n=========Beginning User {self.sub_agent_title} ALtering Agent=========")
        return {}

    # Delete the old children belonging to the current item.
    def delete_old_children(self, state):
        pass

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state):
        pass

    # Print output.
    def get_formatted_list(self, state):
        LogAlteringAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_id = state["user_id"]
        schedule_from_db = self.focus_list_retriever_agent(user_id)

        schedule_dict = [schedule_entry.to_dict() for schedule_entry in schedule_from_db]

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogAlteringAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogAlteringAgent.agent_introductions(f"=========Ending User {self.sub_agent_title} ALtering Agent=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        pass