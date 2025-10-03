from typing_extensions import TypeVar

from langgraph.graph import StateGraph, START, END

from app.agent_states.main_agent_state import MainAgentState

from .base import BaseAgent, confirm_impact, determine_if_alter, determine_if_read

# ----------------------------------------- Base Sub Agent For Schedule Items With Parents -----------------------------------------

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class BaseAgentWithParents(BaseAgent):
    parent_scheduler_agent = None

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

    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
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
                "impact": "parent_agent"                                # Retrieve the parent element if an impact is indicated.
            }
        )

        workflow.add_edge("parent_agent", "extract_operations")

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

        workflow.add_edge("altering_agent", "end_node")
        workflow.add_edge("reading_agent", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()
