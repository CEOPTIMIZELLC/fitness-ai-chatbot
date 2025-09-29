from logging_config import LogMainSubAgent
from typing_extensions import TypeVar
from app.agent_states.main_agent_state import MainAgentState

from .agent import create_main_agent_graph

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class AgentNode():
    def availability_node(self, state: TState):
        LogMainSubAgent.agent_introductions(f"\n=========Starting User Availability=========")
        if state["availability_is_requested"]:
            availability_agent = create_main_agent_graph()
            result = availability_agent.invoke({
                "user_id": state["user_id"], 
                "user_input": state["user_input"], 
                "attempts": state["attempts"], 
                "availability_is_requested": state["availability_is_requested"], 
                "availability_is_alter": state["availability_is_alter"], 
                "availability_is_read": state["availability_is_read"], 
                "availability_read_plural": state["availability_read_plural"], 
                "availability_read_current": state["availability_read_current"], 
                "availability_detail": state["availability_detail"]
            })
        else:
            result = {
                "availability_is_requested": False, 
                "availability_is_alter": False,
                "availability_is_read": False,
                "availability_read_plural": False, 
                "availability_read_current": False, 
                "availability_detail": None, 
                "availability_formatted": None,
                "availability_other_requests": None
            }
        return {
            "availability_is_requested": result["availability_is_requested"], 
            "availability_is_alter": result["availability_is_alter"], 
            "availability_is_read": result["availability_is_read"], 
            "availability_read_plural": result["availability_read_plural"], 
            "availability_read_current": result["availability_read_current"], 
            "availability_detail": result["availability_detail"], 
            "availability_formatted": result["availability_formatted"], 
            "availability_other_requests": result.get("other_requests")
        }
