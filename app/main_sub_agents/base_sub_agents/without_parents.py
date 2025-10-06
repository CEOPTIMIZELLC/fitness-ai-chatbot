from logging_config import LogMainSubAgent

from langgraph.graph import StateGraph, START, END

# Utils imports.
from app.utils.agent_state_helpers import retrieve_current_agent_focus

# Local imports.
from .base import BaseAgent, confirm_impact, determine_if_alter, determine_if_read

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
    if not state.get(f"{sub_agent_focus}_detail", None):
        return "no_new_input"
    return "present_new_input"

class BaseAgentWithoutParents(BaseAgent):
    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("extract_operations", self.extract_operations)
        workflow.add_node("altering_agent", self.altering_agent)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("reading_agent", self.reading_agent)
        workflow.add_node("operation_is_not_read", self.chained_conditional_inbetween)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            confirm_impact, 
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "extract_operations"                          # Determine what operations to perform.
            }
        )

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "extract_operations",
            determine_if_alter, 
            {
                "not_alter": "operation_is_not_alter",                  # In between step for if the operation is not alter.
                "alter": "altering_agent"                               # Start altering subagent.
            }
        )
        workflow.add_edge("altering_agent", "operation_is_not_alter")

        # Whether the goal is to read user elements.
        workflow.add_conditional_edges(
            "operation_is_not_alter",
            determine_if_read, 
            {
                "not_read": "operation_is_not_read",                    # In between step for if the operation is not read.
                "read": "reading_agent"                                 # Start reading subagent.
            }
        )
        workflow.add_edge("reading_agent", "operation_is_not_read")

        workflow.add_edge("operation_is_not_read", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

