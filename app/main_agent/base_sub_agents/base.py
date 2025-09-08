from logging_config import LogMainSubAgent
from flask import abort
from typing_extensions import TypeVar

from app.main_agent.main_agent_state import MainAgentState
from .utils import sub_agent_focused_items

# ----------------------------------------- Base Sub Agent For Schedule Items -----------------------------------------

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class BaseAgent():
    focus = ""
    sub_agent_title = ""
    focus_system_prompt = None
    focus_goal = None
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
        LogMainSubAgent.agent_introductions(f"\n=========Beginning User {self.sub_agent_title} Sub Agent=========")
        return {"focus_name": self.focus}

    # Confirm that the desired section should be impacted.
    def confirm_impact(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Confirm that the {self.sub_agent_title} is Impacted---------")
        if not state[self.focus_names["impact"]]:
            LogMainSubAgent.agent_steps(f"\t---------No Impact---------")
            return "no_impact"
        return "impact"

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        return {
            focus_names["impact"]: goal_class.is_requested,
            focus_names["is_altered"]: True,
            focus_names["read_plural"]: False,
            focus_names["read_current"]: False,
            focus_names["message"]: goal_class.detail,
            "other_requests": goal_class.other_requests
        }

    # Determine the operation to be performed.
    def determine_operation(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to read or write {self.sub_agent_title}---------")
        if state[self.focus_names["is_altered"]]:
            return "alter"
        return "read"

    # Determine whether the outcome is to read the entire schedule or simply the current item.
    def determine_read_operation(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to read a list of {self.sub_agent_title} or simply a singular item---------")
        if state[self.focus_names["read_plural"]]:
            return "plural"
        return "singular"

    # Determine whether the outcome is to read an item from the current set or all items from the user.
    def determine_read_filter_operation(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to read all {self.sub_agent_title} items for the user or only those currently active---------")
        if state[self.focus_names["read_current"]]:
            return "current"
        return "all"

    # Retrieve user's current schedule item.
    def read_user_current_element(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Current {self.sub_agent_title} for User---------")
        user_id = state["user_id"]

        entry_from_db = self.focus_retriever_agent(user_id)
        if not entry_from_db:
            abort(404, description=f"No active {self.sub_agent_title} found.")

        schedule_dict = [entry_from_db.to_dict()]
        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Print output.
    def get_formatted_list(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_id = state["user_id"]
        schedule_from_db = self.focus_list_retriever_agent(user_id)

        schedule_dict = [schedule_entry.to_dict() for schedule_entry in schedule_from_db]

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Print output.
    def get_user_list(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving All {self.sub_agent_title} Schedules---------")
        user_id = state["user_id"]

        schedule_from_db = self.user_list_query(user_id)
        if not schedule_from_db:
            abort(404, description=f"No {self.focus}s found for the user.")

        schedule_dict = [schedule_entry.to_dict() for schedule_entry in schedule_from_db]

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogMainSubAgent.agent_introductions(f"=========Ending User {self.sub_agent_title} SubAgent=========\n")
        return {}