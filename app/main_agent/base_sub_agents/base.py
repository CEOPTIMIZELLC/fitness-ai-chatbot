from logging_config import LogMainSubAgent
from flask import abort

from app.goal_prompts.sub_agent_operations import goal_system_prompt
from app.impact_goal_models.sub_agent_operations import OperationGoals

from app.utils.agent_state_helpers import retrieve_current_agent_focus, sub_agent_focused_items, goal_classifier_parser
from app.utils.user_input import new_input_request

# ----------------------------------------- Base Sub Agent For Schedule Items -----------------------------------------

operations_to_check = [
    "read", 
    "alter", 
    "create", 
    "delete"
]

# Change state switches depending on desired read operation.
def include_read_operation_in_dict(operation_dict, read_operation):
    match(read_operation):
        case "plural":
            operation_dict["read_plural"] = True
            operation_dict["read_current"] = False
        case "current":
            operation_dict["read_plural"] = True
            operation_dict["read_current"] = True
        case _:
            operation_dict["read_plural"] = False
            operation_dict["read_current"] = False
    return operation_dict


def retrieve_read_operation(operation_dict, read_request):
    # Retrieve if the read agent should view a single item, the current list, or the entire user inventory.
    read_operation = read_request.get("read_method", None)
    if read_operation:
        read_operation = read_operation.value
    else:
        read_operation = "singular"

    operation_dict = include_read_operation_in_dict(operation_dict, read_operation)
    return operation_dict

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
    if state.get(f"{sub_agent_focus}_is_delete", False):
        return "deletion"
    return "not_deletion"

# Determine if an item is to be altered.
def determine_if_create(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to create {sub_agent_focus}---------")
    if state.get(f"{sub_agent_focus}_is_create", False):
        return "create"
    return "not_create"

# Determine if an item is to be altered.
def determine_if_alter(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to alter {sub_agent_focus}---------")
    if state.get(f"{sub_agent_focus}_is_alter", False):
        return "alter"
    return "not_alter"

# Determine if an item is to be read.
def determine_if_read(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to read {sub_agent_focus}---------")
    if state.get(f"{sub_agent_focus}_is_read", False):
        return "read"
    return "not_read"

class BaseAgent():
    focus = ""
    sub_agent_title = ""
    focus_system_prompt = None
    focus_goal = None

    altering_agent = None
    creation_agent = None
    deletion_agent = None
    reading_agent = None

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
    
    # Extracts the operation requests from the input.
    def operation_parser(self, state_updates, operation_class, operation_check):

        operation_being_checked = operation_class.get(f"{operation_check}_request", None)

        if operation_being_checked:
            state_updates[f"is_{operation_check}"] = operation_being_checked.get("is_requested", False)
            state_updates[f"{operation_check}_detail"] = operation_being_checked.get("detail", None)
        
        return state_updates
    
    # Performs necessary formatting changes for the subagent before changing the state.
    def format_operations(self, state_updates):
        return state_updates

    # Request permission from user to execute the new input.
    def extract_operations(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Determine what Operation(s) to Perform for User {self.sub_agent_title}---------")
        user_input = state[self.focus_names["detail"]]

        # Retrieve the new input for the focus item.
        operation_class = new_input_request(user_input, goal_system_prompt, OperationGoals)
        operation_class_dump = operation_class.model_dump()

        operation_dict = {}
        state_updates = {}

        for operation_check in operations_to_check:
            self.operation_parser(operation_dict, operation_class_dump, operation_check)
        
        read_request = operation_class_dump.get("read_request", None)
        if read_request:
            operation_dict = retrieve_read_operation(operation_dict, read_request)

        operation_dict = self.format_operations(operation_dict)

        for key, value in operation_dict.items():
            state_updates[self.focus + "_"  + key] = value

        return state_updates

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        return goal_classifier_parser(focus_names, goal_class)

    # Node to declare that the sub agent has ended.
    def end_node(self, state):

        # Remove current agent from the path once it is done.
        agent_path = state.get("agent_path", [])
        agent_path.pop()
        LogMainSubAgent.agent_path(f"Agent Path: {agent_path}")

        end_node_state = {}
        for operation_check in operations_to_check:
            end_node_state[self.focus_names[f"is_{operation_check}"]] = False
            end_node_state[self.focus_names[f"{operation_check}_detail"]] = None
        end_node_state["agent_path"] = agent_path

        LogMainSubAgent.agent_introductions(f"=========Ending User {self.sub_agent_title} SubAgent=========\n")
        return end_node_state

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        pass