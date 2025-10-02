from logging_config import LogMainSubAgent
from flask import abort
from typing_extensions import TypeVar

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app import db
from app.agent_states.main_agent_state import MainAgentState
from app.utils.user_input import new_input_request, user_input_information_extraction

from .base import BaseAgent, confirm_impact, determine_if_alter, determine_if_read
from app.utils.agent_state_helpers import retrieve_current_agent_focus, sub_agent_focused_items, agent_state_update, log_extracted_goals
from app.utils.global_variables import sub_agent_names

# ----------------------------------------- Base Sub Agent For Schedule Items With Parents -----------------------------------------

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

# Confirm that a currently active parent exists to attach the a schedule to.
def confirm_parent(state: TState):
    parent_agent_focus = retrieve_current_agent_focus(state, "parent")
    LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active {parent_agent_focus}---------")
    if not state[f"user_{parent_agent_focus}"]:
        return "no_parent"
    return "parent"

# Router for if permission was granted.
def confirm_permission(state: TState):
    parent_agent_focus = retrieve_current_agent_focus(state, "parent")
    LogMainSubAgent.agent_steps(f"\t---------Confirm the agent can create a new {parent_agent_focus}---------")
    if not state[f"{parent_agent_focus}_is_requested"]:
        return "permission_denied"
    return "permission_granted"

class BaseAgentWithParents(BaseAgent):
    parent = ""
    parent_title = ""
    parent_system_prompt = None
    parent_goal = None
    parent_scheduler_agent = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)
        self.parent_names = sub_agent_focused_items(self.parent)

    def parent_retriever_agent(self, user_id):
        pass

    # Performs necessary formatting changes for the subagent before changing the state.
    def format_operations(self, state_updates):

        # Combine the alter and creation requests since they are synonamous for availability.
        if any(key in state_updates for key in ("is_alter", "is_create")):
            is_alter = state_updates.pop("is_alter", False) or state_updates.pop("is_create", False)
            
            # Combine requests.
            item_request_list = [state_updates.pop("alter_detail", None), state_updates.pop("create_detail", None)]
            alter_detail = " ".join(
                value
                for value in item_request_list
                if value != None
            )

            state_updates["is_alter"] = is_alter
            state_updates["alter_detail"] = alter_detail
        return state_updates

    # Node to declare that the sub agent has begun.
    def start_node(self, state):
        LogMainSubAgent.agent_introductions(f"\n=========Beginning User {self.sub_agent_title} Sub Agent=========")

        # Append the current sub agent to the path.
        agent_path = state.get("agent_path", [])
        agent_path.append({
            "focus": self.focus, 
            "parent": self.parent
        })
        LogMainSubAgent.agent_path(f"Agent Path: {agent_path}")

        return {
            "focus_name": self.focus, 
            "parent_name": self.parent, 
            "agent_path": agent_path
        }

    # Retrieve parent item that will be used for the current schedule.
    def retrieve_parent(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Current {self.parent_title}---------")
        user_id = state["user_id"]
        parent_db_entry = self.parent_retriever_agent(user_id)

        # Return parent.
        return {self.parent_names["entry"]: parent_db_entry.to_dict() if parent_db_entry else None}

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        pass

    # In between node for when the parent is retrieved.
    def parent_retrieved(self, state: TState):
        # Change the parent id if performing it with a different id has been specified.
        perform_with_parent_id_key = self.focus_names["perform_with_parent_id"]
        if perform_with_parent_id_key in state and state[perform_with_parent_id_key]:
            LogMainSubAgent.agent_steps(f"\t---------Change parent id of {self.parent_title}---------")
            user_id = state["user_id"]
            new_parent_id = state[perform_with_parent_id_key]
            parent_db_entry = self.parent_changer(user_id, new_parent_id)

            db.session.commit()

            # Return new parent.
            return {self.parent_names["entry"]: parent_db_entry.to_dict() if parent_db_entry else None}

        return {}

    # Request permission from user to execute the parent initialization.
    def ask_for_permission(self, state: TState):
        # If the permission has already been given, move on ahead.
        if state[self.parent_names["is_requested"]]:
            LogMainSubAgent.agent_steps(f"\t---------Permission already granted---------")
            return {}
        LogMainSubAgent.agent_steps(f"\t---------Ask user if a new {self.parent_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.parent_title} exists for {self.sub_agent_title}. Would you like for me to generate a {self.parent_title} for you?"
        })
        user_input = result["user_input"]

        # Retrieve the new input for the parent item.
        goal_class = new_input_request(user_input, self.parent_system_prompt, self.parent_goal)

        # Parse the structured output values to a dictionary.
        return self.goal_classifier_parser(self.parent_names, goal_class)

    def other_requests_information_extractor(self, state, ignore_section, other_requests="other_requests"):
        # Retrieve the other requests.
        user_input = state.get(other_requests)
        if not user_input:
            LogMainSubAgent.agent_steps(f"\n---------No Other Requests---------")
            return {}

        state_updates = user_input_information_extraction(user_input)
        result = agent_state_update(state, state_updates, ignore_section)
        log_extracted_goals(result)

        # Reset other requests to be empty.
        state[other_requests] = None
        return result

    # Find other requests from the previous parent message retrieval.
    def parent_requests_extraction(self, state: TState):
        LogMainSubAgent.agent_steps(f"\n---------Extract Other Requests---------")
        return self.other_requests_information_extractor(state, self.parent)

    # State if the Parent isn't allowed to be requested.
    def permission_denied(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Abort {self.sub_agent_title} Scheduling---------")
        abort(404, description=f"No active {self.parent_title} found.")
        return {}

    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("ask_for_permission", self.ask_for_permission)
        workflow.add_node("parent_requests_extraction", self.parent_requests_extraction)
        workflow.add_node("permission_denied", self.permission_denied)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
        workflow.add_node("parent_retrieved", self.parent_retrieved)
        workflow.add_node("extract_operations", self.extract_operations)
        workflow.add_node("altering_agent", self.altering_agent)
        workflow.add_node("reading_agent", self.reading_agent)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            confirm_impact, 
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "retrieve_parent"                             # Retrieve the parent element if an impact is indicated.
            }
        )

        # Whether a parent element exists.
        workflow.add_conditional_edges(
            "retrieve_parent",
            confirm_parent, 
            {
                "no_parent": "ask_for_permission",                      # No parent element exists.
                "parent": "parent_retrieved"                            # In between step for if a parent element exists.
            }
        )

        workflow.add_edge("parent_retrieved", "extract_operations")

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "extract_operations",
            determine_if_alter, 
            {
                "not_alter": "operation_is_not_alter",                  # In between step for if the operation is not alter.
                "alter": "altering_agent"                               # Start altering subagent.
            }
        )

        # Whether the goal is to read user elements.
        workflow.add_conditional_edges(
            "operation_is_not_alter",
            determine_if_read, 
            {
                "not_read": "end_node",                                 # End subagent if nothing is requested.
                "read": "reading_agent"                                 # Start reading subagent.
            }
        )

        # Whether a parent element is allowed to be created where one doesn't already exist.
        workflow.add_edge("ask_for_permission", "parent_requests_extraction")
        workflow.add_conditional_edges(
            "parent_requests_extraction",
            confirm_permission, 
            {
                "permission_denied": "permission_denied",               # The agent isn't allowed to create a parent.
                "permission_granted": "parent_agent"                    # The agent is allowed to create a parent.
            }
        )
        workflow.add_edge("parent_agent", "retrieve_parent")

        workflow.add_edge("altering_agent", "end_node")
        workflow.add_edge("reading_agent", "end_node")
        workflow.add_edge("permission_denied", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()
