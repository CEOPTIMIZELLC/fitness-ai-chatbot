from logging_config import LogMainSubAgent
from flask import abort

from langgraph.types import interrupt

from app.goal_prompts.availability import availability_system_prompt
from app.impact_goal_models.availability import AvailabilityGoal
from app.main_agent.user_weekdays_availability import WeekdayAvailabilityAgentNode as AvailabilityNode
from app.utils.user_input import new_input_request

from .with_parents import TState
from .with_parents import BaseAgentWithParents
from app.utils.agent_state_helpers import sub_agent_focused_items, goal_classifier_parser

# ----------------------------------------- Base Sub Agent For Schedule Items With Availability -----------------------------------------

# Confirm that a currently active availability exists to attach the a schedule to.
def confirm_availability(state: TState):
    LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active Availability---------")
    if not state.get("user_availability", None):
        return "no_availability"
    return "availability"

# Router for if permission was granted.
def confirm_availability_permission(state: TState):
    LogMainSubAgent.agent_steps(f"\t---------Confirm the agent can create a new Availability---------")
    if not state.get("availability_is_requested", False):
        return "permission_denied"
    return "permission_granted"

class BaseAgentWithAvailability(AvailabilityNode, BaseAgentWithParents):
    availability_focus = "availability"
    sub_agent_title = ""
    availability_title = "Availability"
    availability_system_prompt = availability_system_prompt
    availability_goal = AvailabilityGoal

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)
        self.parent_names = sub_agent_focused_items(self.parent)
        self.availability_names = sub_agent_focused_items(self.availability_focus)

    def availability_retriever_agent(self, state: TState):
        pass

    # Retrieve availability item that will be used for the current schedule.
    def retrieve_availability(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving {self.availability_title} for {self.sub_agent_title} Scheduling---------")
        return self.availability_retriever_agent(state)

    # Request permission from user to execute the availability initialization.
    def ask_for_availability_permission(self, state: TState):
        # If the permission has already been given, move on ahead.
        if state[self.availability_names["is_requested"]]:
            LogMainSubAgent.agent_steps(f"\t---------Permission already granted---------")
            return {}
        LogMainSubAgent.agent_steps(f"\t---------Ask user if a new {self.availability_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.availability_title} exists. Would you like for me to generate a {self.availability_title} for you?"
        })
        user_input = result["user_input"]

        # Retrieve the new input for the focus item.
        goal_class = new_input_request(user_input, self.availability_system_prompt, self.availability_goal)

        # Parse the structured output values to a dictionary.
        return goal_classifier_parser(self.availability_names, goal_class, f"availability_other_requests")

    # Request is unique for Availability retrieval
    def availability_requests_extraction(self, state: TState):
        LogMainSubAgent.agent_steps(f"\n---------Extract Other Requests for Availability---------")
        return self.other_requests_information_extractor(state, self.availability_focus, f"availability_other_requests")

    # State if the Availability isn't allowed to be requested.
    def availability_permission_denied(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Abort {self.sub_agent_title} Scheduling---------")
        abort(404, description=f"No active {self.availability_title} found.")
        return {}


