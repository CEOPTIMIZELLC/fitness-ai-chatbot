from logging_config import LogMainSubAgent
from flask import abort
from .utils import retrieve_current_agent_focus, sub_agent_focused_items

# ----------------------------------------- Base Sub Agent For Schedule Items -----------------------------------------

# Confirm that the desired section should be impacted.
def confirm_impact(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Confirm that the {sub_agent_focus} is Impacted---------")
    if not state.get(f"{sub_agent_focus}_is_requested", False):
        LogMainSubAgent.agent_steps(f"\t---------No Impact---------")
        return "no_impact"
    return "impact"

# Determine if an item is to be deleted.
def determine_if_delete(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to delete {sub_agent_focus}---------")
    if state.get(f"{sub_agent_focus}_delete_old", False):
        return "deletion"
    return "not_deletion"

# Determine if an item is to be altered.
def determine_if_create(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to create {sub_agent_focus}---------")
    if state.get(f"{sub_agent_focus}_is_altered", False) and not state.get(f"{sub_agent_focus}_alter_old", False):
        return "create"
    return "not_create"

# Determine if an item is to be altered.
def determine_if_alter(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to alter {sub_agent_focus}---------")
    if state.get(f"{sub_agent_focus}_is_altered", False):
        return "alter"
    return "not_alter"

# Determine if an item is to be read.
def determine_if_read(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to read {sub_agent_focus}---------")
    if state.get(f"{sub_agent_focus}_is_read", False):
        return "read"
    return "not_read"

# Determine whether the outcome is to read the entire schedule or simply the current item.
def determine_read_operation(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to read a list of {sub_agent_focus} or simply a singular item---------")
    if state.get(f"{sub_agent_focus}_read_plural", False):
        return "plural"
    return "singular"

# Determine whether the outcome is to read an item from the current set or all items from the user.
def determine_read_filter_operation(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to read all {sub_agent_focus} items for the user or only those currently active---------")
    if state.get(f"{sub_agent_focus}_read_current", False):
        return "current"
    return "all"

# Determine whether the schedule should be regenerated.
def confirm_regenerate(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the {sub_agent_focus} schedule should be regenerated---------")
    if state.get("is_regenerated", False):
        LogMainSubAgent.agent_steps(f"\t---------Is Regenerated---------")
        return "is_regenerated"
    return "not_regenerated"

class BaseAgent():
    focus = ""
    sub_agent_title = ""
    focus_system_prompt = None
    focus_goal = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)

    # In between node for chained conditional edges.
    def chained_conditional_inbetween(self, state):
        return {}
    
    # Node to declare that the sub agent has begun.
    def start_node(self, state):
        LogMainSubAgent.agent_introductions(f"\n=========Beginning User {self.sub_agent_title} Sub Agent=========")

        # Append the current sub agent to the path.
        agent_path = state.get("agent_path", [])
        agent_path.append({"focus": self.focus})
        LogMainSubAgent.agent_path(f"Agent Path: {agent_path}")

        return {
            "focus_name": self.focus, 
            "agent_path": agent_path
        }

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        goal_class_dump = goal_class.model_dump()
        parsed_goal = {
            focus_names["is_altered"]: True,
            focus_names["read_plural"]: False,
            focus_names["read_current"]: False,
            "other_requests": goal_class_dump.pop("other_requests", None)
        }

        # Alter the variables in the state to match those retrieved from the LLM.
        for key, value in goal_class_dump.items():
            if value is not None:
                parsed_goal[focus_names[key]] = value

        return parsed_goal

    # Node to declare that the sub agent has ended.
    def end_node(self, state):

        # Remove current agent from the path once it is done.
        agent_path = state.get("agent_path", [])
        agent_path.pop()
        LogMainSubAgent.agent_path(f"Agent Path: {agent_path}")

        LogMainSubAgent.agent_introductions(f"=========Ending User {self.sub_agent_title} SubAgent=========\n")
        return {
            "agent_path": agent_path
        }

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        pass