from logging_config import LogMainSubAgent
from flask import abort

from langgraph.types import interrupt

from .base import BaseAgent
from .utils import new_input_request

# ----------------------------------------- Base Sub Agent For Schedule Items Without Parents -----------------------------------------

# Check if a new goal exists to be classified.
def confirm_if_performing_by_id(state):
    current_subagent_place = state["agent_path"][-1]
    sub_agent_focus = current_subagent_place["focus"]

    LogMainSubAgent.agent_steps(f"\t---------Confirm that the {sub_agent_focus} input is meant to just use an ID.---------")
    perform_with_parent_id_key = f"{sub_agent_focus}_perform_with_parent_id"
    if perform_with_parent_id_key in state and state[perform_with_parent_id_key]:
        return "present_direct_goal_id"
    return "no_direct_goal_id"

# Check if a new goal exists to be classified.
def confirm_new_input(state):
    current_subagent_place = state["agent_path"][-1]
    sub_agent_focus = current_subagent_place["focus"]

    LogMainSubAgent.agent_steps(f"\t---------Confirm there is a new {sub_agent_focus} input to be parsed---------")
    if not state[f"{sub_agent_focus}_message"]:
        return "no_new_input"
    return "present_new_input"

class BaseAgentWithoutParents(BaseAgent):
    # Request permission from user to execute the new input.
    def ask_for_new_input(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Ask user if a new {self.sub_agent_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.sub_agent_title} exists. Would you like for me to generate a {self.sub_agent_title} for you?"
        })
        user_input = result["user_input"]
        LogMainSubAgent.verbose(f"Extract the {self.sub_agent_title} Goal the following message: {user_input}")

        # Retrieve the new input for the focus item.
        goal_class = new_input_request(user_input, self.focus_system_prompt, self.focus_goal)

        # Parse the structured output values to a dictionary.
        return self.goal_classifier_parser(self.focus_names, goal_class)

    # State if no new input was requested.
    def no_new_input_requested(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Abort {self.sub_agent_title} Parsing---------")
        abort(404, description=f"No active {self.sub_agent_title} requested.")
        return {}

    def perform_input_parser(self, state):
        pass

    # Delete the old children belonging to the current item.
    def delete_old_children(self, state):
        pass

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state):
        pass

