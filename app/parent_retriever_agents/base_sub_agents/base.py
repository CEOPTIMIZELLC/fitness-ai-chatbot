from logging_config import LogParentSubAgent
from flask import abort
from typing_extensions import TypeVar

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

# Utils imports.
from app.utils.agent_state_helpers import (
    retrieve_current_agent_focus, 
    sub_agent_focused_items, 
    agent_state_update, 
    log_extracted_goals, 
    goal_classifier_parser
)
from app.utils.user_input import new_input_request, user_input_information_extraction

# Database imports.
from app import db

# Agent construction imports.
from app.agent_states.main_agent_state import MainAgentState

# ----------------------------------------- Base Sub Agent For Schedule Items -----------------------------------------

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

# Confirm that a currently active parent exists to attach the a schedule to.
def confirm_parent(state: TState):
    parent_agent_focus = retrieve_current_agent_focus(state, "parent")
    LogParentSubAgent.agent_steps(f"\t---------Confirm there is an active {parent_agent_focus}---------")
    if not state.get(f"user_{parent_agent_focus}", None):
        return "no_parent"
    return "parent"

# Router for if permission was granted.
def confirm_permission(state: TState):
    parent_agent_focus = retrieve_current_agent_focus(state, "parent")
    LogParentSubAgent.agent_steps(f"\t---------Confirm the agent can create a new {parent_agent_focus}---------")
    if not state.get(f"{parent_agent_focus}_is_requested", False):
        return "permission_denied"
    return "permission_granted"

class BaseAgent():
    focus = ""
    sub_agent_title = ""
    focus_system_prompt = None
    focus_goal = None
    parent = ""
    parent_title = ""
    parent_system_prompt = None
    parent_goal = None
    parent_scheduler_agent = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)
        self.parent_names = sub_agent_focused_items(self.parent)

    # In between node for chained conditional edges.
    def chained_conditional_inbetween(self, state):
        return {}
    
    # Node to declare that the sub agent has begun.
    def start_node(self, state):
        LogParentSubAgent.agent_introductions(f"\n=========Beginning User {self.sub_agent_title} Parent ({self.parent_title}) Sub Agent=========")

        # Append the current sub agent to the path.
        agent_path = state.get("agent_path", [])
        agent_path.append({
            "focus": self.focus, 
            "parent": self.parent
        })
        LogParentSubAgent.agent_path(f"Agent Path: {agent_path}")

        return {
            "focus_name": self.focus, 
            "parent_name": self.parent, 
            "agent_path": agent_path
        }

    def parent_retriever_agent(self, user_id):
        pass

    # Retrieve parent item that will be used for the current schedule.
    def retrieve_parent(self, state: TState):
        LogParentSubAgent.agent_steps(f"\t---------Retrieving Current {self.parent_title}---------")
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
            LogParentSubAgent.agent_steps(f"\t---------Change parent id of {self.parent_title}---------")
            user_id = state["user_id"]
            new_parent_id = state[perform_with_parent_id_key]
            parent_db_entry = self.parent_changer(user_id, new_parent_id)

            db.session.commit()

            # Return new parent.
            return {self.parent_names["entry"]: parent_db_entry.to_dict() if parent_db_entry else None}

        return {}


    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        return goal_classifier_parser(focus_names, goal_class)

    # Request permission from user to execute the parent initialization.
    def ask_for_permission(self, state: TState):
        # If the permission has already been given, move on ahead.
        if state[self.parent_names["is_requested"]]:
            LogParentSubAgent.agent_steps(f"\t---------Permission already granted---------")
            return {}
        LogParentSubAgent.agent_steps(f"\t---------Ask user if a new {self.parent_title} can be made---------")
        result = interrupt({
            "task": [f"No current {self.parent_title} exists for {self.sub_agent_title}. Would you like for me to generate a {self.parent_title} for you?"]
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
            LogParentSubAgent.agent_steps(f"\n---------No Other Requests---------")
            return {}

        state_updates = user_input_information_extraction(user_input)
        result = agent_state_update(state, state_updates, ignore_section)
        log_extracted_goals(result)

        # Reset other requests to be empty.
        state[other_requests] = None
        return result

    # Find other requests from the previous parent message retrieval.
    def parent_requests_extraction(self, state: TState):
        LogParentSubAgent.agent_steps(f"\n---------Extract Other Requests---------")
        return self.other_requests_information_extractor(state, self.parent)

    # State if the Parent isn't allowed to be requested.
    def permission_denied(self, state: TState):
        LogParentSubAgent.agent_steps(f"\t---------Abort {self.sub_agent_title} Scheduling---------")
        abort(404, description=f"No active {self.parent_title} found.")
        return {}

    # Node to declare that the sub agent has ended.
    def end_node(self, state):

        # Remove current agent from the path once it is done.
        agent_path = state.get("agent_path", [])
        agent_path.pop()
        LogParentSubAgent.agent_path(f"Agent Path: {agent_path}")

        # Reset requests to prevent looping requests.
        end_node_state = {}
        end_node_state["agent_path"] = agent_path

        LogParentSubAgent.agent_introductions(f"=========Ending User {self.sub_agent_title} Parent ({self.parent_title}) Sub Agent=========\n")
        return end_node_state

    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("ask_for_permission", self.ask_for_permission)
        workflow.add_node("parent_requests_extraction", self.parent_requests_extraction)
        workflow.add_node("permission_denied", self.permission_denied)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
        workflow.add_node("parent_retrieved", self.parent_retrieved)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "retrieve_parent")

        # Whether a parent element exists.
        workflow.add_conditional_edges(
            "retrieve_parent",
            confirm_parent, 
            {
                "no_parent": "ask_for_permission",                      # No parent element exists.
                "parent": "parent_retrieved"                            # In between step for if a parent element exists.
            }
        )

        workflow.add_edge("parent_retrieved", "end_node")


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

        workflow.add_edge("permission_denied", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()
