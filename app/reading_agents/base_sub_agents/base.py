from logging_config import LogReadingAgent
from flask import abort
from .utils import retrieve_current_agent_focus, sub_agent_focused_items

# ----------------------------------------- Base Sub Agent For Schedule Items -----------------------------------------

# Determine whether the outcome is to read the entire schedule or simply the current item.
def determine_read_operation(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogReadingAgent.agent_steps(f"\t---------Determine if the objective is to read a list of {sub_agent_focus} or simply a singular item---------")
    if state[f"{sub_agent_focus}_read_plural"]:
        return "plural"
    return "singular"

# Determine whether the outcome is to read an item from the current set or all items from the user.
def determine_read_filter_operation(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogReadingAgent.agent_steps(f"\t---------Determine if the objective is to read all {sub_agent_focus} items for the user or only those currently active---------")
    if state[f"{sub_agent_focus}_read_current"]:
        return "current"
    return "all"

class BaseAgent():
    focus = ""
    sub_agent_title = ""
    schedule_printer_class = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)

    def user_list_query(self, user_id):
        pass

    def focus_retriever_agent(self, user_id):
        pass

    def focus_list_retriever_agent(self, user_id):
        pass

    # In between node for chained conditional edges.
    def chained_conditional_inbetween(self, state):
        return {}
    
    # Node to declare that the sub agent has begun.
    def start_node(self, state):
        LogReadingAgent.agent_introductions(f"\n=========Beginning User {self.sub_agent_title} Sub Agent=========")
        return {}

    # Retrieve user's current schedule item.
    def read_user_current_element(self, state):
        LogReadingAgent.agent_steps(f"\t---------Retrieving Current {self.sub_agent_title} for User---------")
        user_id = state["user_id"]

        entry_from_db = self.focus_retriever_agent(user_id)
        if not entry_from_db:
            abort(404, description=f"No active {self.sub_agent_title} found.")

        schedule_dict = [entry_from_db.to_dict()]
        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogReadingAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Print output.
    def get_formatted_list(self, state):
        LogReadingAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_id = state["user_id"]
        schedule_from_db = self.focus_list_retriever_agent(user_id)

        schedule_dict = [schedule_entry.to_dict() for schedule_entry in schedule_from_db]

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogReadingAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Print output.
    def get_user_list(self, state):
        LogReadingAgent.agent_steps(f"\t---------Retrieving All {self.sub_agent_title} Schedules---------")
        user_id = state["user_id"]

        schedule_from_db = self.user_list_query(user_id)

        schedule_dict = [schedule_entry.to_dict() for schedule_entry in schedule_from_db]

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogReadingAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogReadingAgent.agent_introductions(f"=========Ending User {self.sub_agent_title} SubAgent=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        pass