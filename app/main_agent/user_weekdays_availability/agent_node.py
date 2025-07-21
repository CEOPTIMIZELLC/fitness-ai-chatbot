from typing_extensions import TypeVar
from app.main_agent.main_agent_state import MainAgentState

from .agent import create_main_agent_graph

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class AgentNode():
    def availability_node(self, state: TState):
        print(f"\n=========Starting User Availability=========")
        if state["availability_impacted"]:
            availability_agent = create_main_agent_graph()
            result = availability_agent.invoke({
                "user_id": state["user_id"], 
                "user_input": state["user_input"], 
                "attempts": state["attempts"], 
                "availability_impacted": state["availability_impacted"], 
                "availability_is_altered": state["availability_is_altered"], 
                "availability_read_plural": state["availability_read_plural"], 
                "availability_read_current": state["availability_read_current"], 
                "availability_message": state["availability_message"]
            })
        else:
            result = {
                "availability_impacted": False, 
                "availability_is_altered": False,
        "availability_read_plural": True,
        "availability_read_current": True, 
                "availability_read_plural": False, 
                "availability_read_current": False, 
                "availability_message": None, 
                "availability_formatted": None
            }
        return {
            "availability_impacted": result["availability_impacted"], 
            "availability_is_altered": result["availability_is_altered"], 
            "availability_read_plural": result["availability_read_plural"], 
            "availability_read_current": result["availability_read_current"], 
            "availability_message": result["availability_message"], 
            "availability_formatted": result["availability_formatted"]
        }
