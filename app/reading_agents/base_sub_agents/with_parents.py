from flask import abort

from langgraph.graph import StateGraph, START, END

from .base import BaseAgent, determine_read_operation, determine_read_filter_operation
from app.utils.agent_state_helpers import sub_agent_focused_items

# ----------------------------------------- Base Sub Agent For Schedule Items With Parents -----------------------------------------

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

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("read_operation_is_plural", self.chained_conditional_inbetween)
        workflow.add_node("read_user_current_element", self.read_user_current_element)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "operation_is_read")

        # Whether the read operations is for a single element or plural elements.
        workflow.add_conditional_edges(
            "operation_is_read",
            determine_read_operation, 
            {
                "plural": "read_operation_is_plural",                   # In between step for if the read operation is plural.
                "singular": "read_user_current_element"                 # Read the current element.
            }
        )

        # Whether the plural list is for all of the elements or all elements belonging to the user.
        workflow.add_conditional_edges(
            "read_operation_is_plural",
            determine_read_filter_operation, 
            {
                "current": "get_formatted_list",                        # Read the current schedule.
                "all": "get_user_list"                                  # Read all user elements.
            }
        )

        workflow.add_edge("read_user_current_element", "end_node")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()
