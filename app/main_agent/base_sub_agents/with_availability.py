from logging_config import LogMainSubAgent
from flask import abort

from langgraph.types import interrupt

from app.goal_prompts import availability_system_prompt
from app.impact_goal_models import AvailabilityGoal
from app.main_agent.user_weekdays_availability import WeekdayAvailabilityAgentNode as AvailabilityNode

from .with_parents import TState
from .with_parents import BaseAgentWithParents
from .utils import sub_agent_focused_items, new_input_request

# ----------------------------------------- Base Sub Agent For Schedule Items With Availability -----------------------------------------

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

    # Confirm that a currently active availability exists to attach the a schedule to.
    def confirm_availability(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active {self.availability_title}---------")
        if not state[self.availability_names["entry"]]:
            return "no_availability"
        return "availability"

    # Request permission from user to execute the availability initialization.
    def ask_for_availability_permission(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Ask user if a new {self.availability_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.availability_title} exists. Would you like for me to generate a {self.availability_title} for you?"
        })
        user_input = result["user_input"]
        LogMainSubAgent.verbose(f"Extract the {self.availability_title} Goal the following message: {user_input}")

        # Retrieve the new input for the focus item.
        goal_class = new_input_request(user_input, self.availability_system_prompt, self.availability_goal)

        # Parse the structured output values to a dictionary.
        return {
            self.availability_names["impact"]: goal_class.is_requested,
            self.availability_names["is_altered"]: True,
            self.availability_names["read_plural"]: False,
            self.availability_names["read_current"]: False,
            self.availability_names["message"]: goal_class.detail
        }

    # Router for if permission was granted.
    def confirm_availability_permission(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Confirm the agent can create a new {self.availability_title}---------")
        if not state[self.availability_names["impact"]]:
            return "permission_denied"
        return "permission_granted"

    # State if the Availability isn't allowed to be requested.
    def availability_permission_denied(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Abort {self.sub_agent_title} Scheduling---------")
        abort(404, description=f"No active {self.availability_title} found.")
        return {}


