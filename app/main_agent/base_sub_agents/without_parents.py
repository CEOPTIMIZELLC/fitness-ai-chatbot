from logging_config import LogMainSubAgent

from .base import BaseAgent
from .utils import retrieve_current_agent_focus

# ----------------------------------------- Base Sub Agent For Schedule Items Without Parents -----------------------------------------

# Check if a new goal exists to be classified.
def confirm_if_performing_by_id(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Confirm that the {sub_agent_focus} input is meant to just use an ID.---------")
    perform_with_parent_id_key = f"{sub_agent_focus}_perform_with_parent_id"
    if perform_with_parent_id_key in state and state[perform_with_parent_id_key]:
        return "present_direct_goal_id"
    return "no_direct_goal_id"

# Check if a new goal exists to be classified.
def confirm_new_input(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogMainSubAgent.agent_steps(f"\t---------Confirm there is a new {sub_agent_focus} input to be parsed---------")
    if not state[f"{sub_agent_focus}_detail"]:
        return "no_new_input"
    return "present_new_input"

class BaseAgentWithoutParents(BaseAgent):
    def perform_input_parser(self, state):
        pass

