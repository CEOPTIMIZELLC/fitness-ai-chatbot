from logging_config import LogDeletionAgent
from flask import abort
from .utils import sub_agent_focused_items

# ----------------------------------------- Base Sub Agent For Schedule Items -----------------------------------------

class BaseAgent():
    focus = ""
    sub_agent_title = ""
    focus_system_prompt = None
    focus_goal = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)

    # In between node for chained conditional edges.
    def chained_conditional_inbetween(self, state):
        return {}
    
    # Node to declare that the sub agent has begun.
    def start_node(self, state):
        LogDeletionAgent.agent_introductions(f"\n=========Beginning User {self.sub_agent_title} Deletion Agent=========")
        return {}

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogDeletionAgent.agent_introductions(f"=========Ending User {self.sub_agent_title} Deletion Agent=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        pass