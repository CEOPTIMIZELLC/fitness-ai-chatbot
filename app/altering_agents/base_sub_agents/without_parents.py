from logging_config import LogAlteringAgent
from flask import abort

from langgraph.types import interrupt

from app.utils.user_input import new_input_request

from .base import BaseAgent
from app.utils.agent_state_helpers import retrieve_current_agent_focus

# ----------------------------------------- Base Sub Agent For Schedule Items Without Parents -----------------------------------------

# Check if a new goal exists to be classified.
def confirm_new_input(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogAlteringAgent.agent_steps(f"\t---------Confirm there is a new {sub_agent_focus} input to be parsed---------")
    if not state[f"{sub_agent_focus}_detail"]:
        return "no_new_input"
    return "present_new_input"

class BaseAgentWithoutParents(BaseAgent):
    focus_system_prompt = None
    focus_goal = None

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        goal_class_dump = goal_class.model_dump()
        parsed_goal = {
            "other_requests": goal_class_dump.pop("other_requests", None)
        }

        # Alter the variables in the state to match those retrieved from the LLM.
        for key, value in goal_class_dump.items():
            if value is not None:
                parsed_goal[focus_names[key]] = value

        return parsed_goal

    # Request permission from user to execute the new input.
    def ask_for_new_input(self, state):
        LogAlteringAgent.agent_steps(f"\t---------Ask user if a new {self.sub_agent_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.sub_agent_title} exists. Would you like for me to generate a {self.sub_agent_title} for you?"
        })
        user_input = result["user_input"]
        LogAlteringAgent.verbose(f"Extract the {self.sub_agent_title} Goal the following message: {user_input}")

        # Retrieve the new input for the focus item.
        goal_class = new_input_request(user_input, self.focus_system_prompt, self.focus_goal)

        # Parse the structured output values to a dictionary.
        return self.goal_classifier_parser(self.focus_names, goal_class)

    # State if no new input was requested.
    def no_new_input_requested(self, state):
        LogAlteringAgent.agent_steps(f"\t---------Abort {self.sub_agent_title} Parsing---------")
        abort(404, description=f"No active {self.sub_agent_title} requested.")
        return {}

    def perform_input_parser(self, state):
        pass

