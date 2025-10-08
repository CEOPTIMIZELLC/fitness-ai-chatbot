from logging_config import LogCreationAgent

from flask import abort

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypeVar

# Utils imports.
from app.utils.agent_state_helpers import sub_agent_focused_items

# Agent construction imports.
from app.agent_states.main_agent_state import MainAgentState

# Local imports.
from .base import BaseAgent, confirm_regenerate

# ----------------------------------------- Base Sub Agent For Schedule Items With Parents -----------------------------------------

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class BaseAgentWithParents(BaseAgent):
    parent = ""

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)
        self.parent_names = sub_agent_focused_items(self.parent)

    def parent_retriever_agent(self, user_id):
        pass

    def retrieve_children_entries_from_parent(self, parent_db_entry):
        pass

    # Focus List Retriever uses the parent retriever and then retrieves the children from it.
    def focus_list_retriever_agent(self, user_id):
        parent_db_entry = self.parent_retriever_agent(user_id)

        schedule_from_db = self.retrieve_children_entries_from_parent(parent_db_entry)
        if not schedule_from_db:
            abort(404, description=f"No {self.focus}s found for the {self.parent}.")
        return schedule_from_db

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: TState):
        pass

    def delete_children_query(self, parent_id):
        pass

    # Delete the old items belonging to the parent.
    def delete_old_children(self, state: TState):
        LogCreationAgent.agent_steps(f"\t---------Delete old {self.sub_agent_title}s---------")
        parent_id = state[self.parent_names["id"]]
        self.delete_children_query(parent_id)
        LogCreationAgent.verbose("Successfully deleted")
        return {}

    # Initializes the scheduler for the current parent.
    def perform_scheduler(self, state: TState):
        pass

    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("perform_scheduler", self.perform_scheduler)
        workflow.add_node("agent_output_to_sqlalchemy_model", self.agent_output_to_sqlalchemy_model)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "retrieve_information")

        workflow.add_edge("retrieve_information", "delete_old_children")
        workflow.add_edge("delete_old_children", "perform_scheduler")

        # Add the editor agent to the path if there is one.
        if self.is_edited:
            workflow.add_node("editor_agent", self.focus_edit_agent)

            workflow.add_edge("perform_scheduler", "editor_agent")

            # Whether the scheduler should be performed again.
            workflow.add_conditional_edges(
                "editor_agent",
                confirm_regenerate, 
                {
                    "is_regenerated": "perform_scheduler",                  # Perform the scheduler again if regenerating.
                    "not_regenerated": "agent_output_to_sqlalchemy_model"   # The agent should move on to adding the information to the database.
                }
            )
        
        else:
            workflow.add_edge("perform_scheduler", "agent_output_to_sqlalchemy_model")

        workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()