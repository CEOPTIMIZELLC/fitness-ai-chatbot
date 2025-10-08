from logging_config import LogEditorAgent

from typing_extensions import TypeVar

from langgraph.graph import StateGraph, START, END

from .base import BaseSubAgent, confirm_edits, confirm_interest
from .base import AgentState as BaseAgentState

class AgentState(BaseAgentState):
    is_regenerated: bool
    should_regenerate: bool

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=AgentState)

# Confirm that the desired section should be edited.
def confirm_regenerate(state):
    LogEditorAgent.agent_steps(f"\t---------Confirm that the Schedule is Regenerated---------")
    if state["is_regenerated"]:
        LogEditorAgent.agent_steps(f"\t---------Is Regenerated---------")
        return "is_regenerated"
    return "not_regenerated"

class BaseSubAgentRegenerate(BaseSubAgent):
    # Items extracted from the edit request.
    def goal_edit_request_parser(self, goal_class, edits_to_be_applyed):
        return {
            "is_edited": True if edits_to_be_applyed else False,
            "edits": edits_to_be_applyed,
            "is_regenerated": goal_class.regenerate,
            "other_requests": goal_class.other_requests
        }

    # In between node for chained conditional edges.
    def chained_conditional_inbetween(self, state):
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class: type[TState] = AgentState):
        workflow = StateGraph(state_class)
        workflow.add_node("format_proposed_list", self.format_proposed_list)
        workflow.add_node("ask_for_edits", self.ask_for_edits)
        workflow.add_node("schedule_not_regenerated", self.chained_conditional_inbetween)
        workflow.add_node("perform_edits", self.perform_edits)
        workflow.add_node("format_proposed_edited_list", self.format_proposed_edited_list)
        workflow.add_node("check_if_schedule_is_valid", self.check_if_schedule_is_valid)
        workflow.add_node("ask_to_move_forward", self.ask_to_move_forward)
        workflow.add_node("finalize_edits", self.finalize_edits)
        workflow.add_node("end_node", self.end_node)

        # Create a formatted list for the user to review.
        workflow.add_edge(START, "format_proposed_list")
        workflow.add_edge("format_proposed_list", "ask_for_edits")

        # Whether the schedule should be regenerated.
        workflow.add_conditional_edges(
            "ask_for_edits",
            confirm_regenerate,
            {
                "is_regenerated": "end_node",                           # The agent should end to allow the main agent to regenerate the schedule.
                "not_regenerated": "schedule_not_regenerated"           # The agent should move on to editing if it wasn't regenerated.
            }
        )

        # Whether any edits have been applied.
        workflow.add_conditional_edges(
            "schedule_not_regenerated",
            confirm_edits,
            {
                "is_edited": "perform_edits",                           # The agent should apply the desired edits to the schedule.
                "not_edited": "end_node"                                # The agent should end if no edits were found.
            }
        )

        workflow.add_edge("perform_edits", "format_proposed_edited_list")
        workflow.add_edge("format_proposed_edited_list", "check_if_schedule_is_valid")
        workflow.add_edge("check_if_schedule_is_valid", "ask_to_move_forward")

        # Whether the user wants to move forward with the new schedule.
        workflow.add_conditional_edges(
            "ask_to_move_forward",
            confirm_interest,
            {
                "allow_schedule": "finalize_edits",                      # The agent should finalize the edits.
                "do_not_allow_schedule": "ask_for_edits"                 # The agent should go back to the edit request.
            }
        )

        workflow.add_edge("finalize_edits", "ask_for_edits")

        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = BaseSubAgentRegenerate()
    return agent.create_main_agent_graph()