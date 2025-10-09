from logging_config import LogMainSubAgent
from typing_extensions import TypeVar
from app.agent_states.main_agent_state import MainAgentState

from .agent import create_main_agent_graph

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class AgentNode():
    def availability_node(self, state: TState):
        LogMainSubAgent.agent_introductions(f"\n=========Starting User Availability=========")
        if state.get("availability_is_requested", False):
            availability_agent = create_main_agent_graph()
            result = availability_agent.invoke({
                "user_id": state["user_id"], 
                "user_input": state.get("user_input", None), 
                "attempts": state.get("attempts", 0), 
                "availability_is_requested": state.get("availability_is_requested", False), 
                "availability_detail": state.get("availability_detail", None)
            })
        else:
            result = {
                "availability_is_requested": False, 
                "availability_detail": None, 
                "availability_formatted": None,
                "availability_list_output": [],
                "availability_other_requests": None
            }
        return {
            "availability_is_requested": result.get("availability_is_requested", False), 
            "availability_detail": result.get("availability_detail", None), 
            "availability_formatted": result.get("availability_formatted", None), 
            "availability_list_output": result.get("availability_list_output", []), 
            "availability_other_requests": result.get("other_requests", None)
        }
