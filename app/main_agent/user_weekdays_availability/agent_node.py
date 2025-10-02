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
                "user_input": state["user_input"], 
                "attempts": state["attempts"], 
                "availability_is_requested": state["availability_is_requested"], 
                "availability_detail": state["availability_detail"]
            })
        else:
            result = {
                "availability_is_requested": False, 
                "availability_detail": None, 
                "availability_formatted": None,
                "availability_other_requests": None
            }
        return {
            "availability_is_requested": result["availability_is_requested"], 
            "availability_detail": result["availability_detail"], 
            "availability_formatted": result["availability_formatted"], 
            "availability_other_requests": result.get("other_requests")
        }
