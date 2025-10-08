from logging_config import LogAlteringAgent
from flask import abort

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

# Utils imports.
from app.utils.agent_state_helpers import retrieve_current_agent_focus, goal_classifier_parser
from app.utils.user_input import new_input_request

# Local imports.
from .base import BaseAgent

# ----------------------------------------- Base Sub Agent For Schedule Items Without Parents -----------------------------------------

# Check if a new goal exists to be classified.
def confirm_new_input(state):
    sub_agent_focus = retrieve_current_agent_focus(state)
    LogAlteringAgent.agent_steps(f"\t---------Confirm there is a new {sub_agent_focus} input to be parsed---------")
    if not state.get(f"{sub_agent_focus}_detail", None):
        return "no_new_input"
    return "present_new_input"

class BaseAgentWithoutParents(BaseAgent):
    focus_system_prompt = None
    focus_goal = None

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        return goal_classifier_parser(focus_names, goal_class)

    # Request permission from user to execute the new input.
    def ask_for_new_input(self, state):
        LogAlteringAgent.agent_steps(f"\t---------Ask user if a new {self.sub_agent_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.sub_agent_title} exists. Would you like for me to generate a {self.sub_agent_title} for you?"
        })
        user_input = result["user_input"]

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


    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("operation_is_alter", self.chained_conditional_inbetween)
        workflow.add_node("ask_for_new_input", self.ask_for_new_input)
        workflow.add_node("perform_input_parser", self.perform_input_parser)
        workflow.add_node("editor_agent", self.focus_edit_agent)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("agent_output_to_sqlalchemy_model", self.agent_output_to_sqlalchemy_model)
        workflow.add_node("no_new_input_requested", self.no_new_input_requested)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "operation_is_alter")

        # Whether there is a new goal to perform the change with.
        workflow.add_conditional_edges(
            "operation_is_alter",
            confirm_new_input, 
            {
                "no_new_input": "ask_for_new_input",                    # Request a new macrocycle goal if one isn't present.
                "present_new_input": "perform_input_parser"             # Parse the goal for what category it falls into if one is present.
            }
        )

        # Whether there is a new goal to perform the change with.
        workflow.add_conditional_edges(
            "ask_for_new_input",
            confirm_new_input, 
            {
                "no_new_input": "no_new_input_requested",               # Indicate that no new goal was given.
                "present_new_input": "perform_input_parser"             # Parse the goal for what category it falls into if one is present.
            }
        )

        workflow.add_edge("perform_input_parser", "editor_agent")
        workflow.add_edge("editor_agent", "delete_old_children")
        workflow.add_edge("delete_old_children", "agent_output_to_sqlalchemy_model")
        workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("no_new_input_requested", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()