from logging_config import LogMainSubAgent
from typing_extensions import TypeVar
from app.agent_states.main_agent_state import MainAgentState

from .agent import create_main_agent_graph

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class AgentNode():
    def macrocycle_node(self, state: TState):
        LogMainSubAgent.agent_introductions(f"\n=========Starting User Macrocycle=========")
        if state.get("macrocycle_is_requested", False):
            goal_agent = create_main_agent_graph()
            result = goal_agent.invoke({
                "user_id": state["user_id"], 
                "user_input": state.get("user_input", None), 
                "attempts": state.get("attempts", 0), 
                "macrocycle_is_requested": state.get("macrocycle_is_requested", False), 
                "macrocycle_detail": state.get("macrocycle_detail", None),
                "macrocycle_perform_with_parent_id": state.get("macrocycle_perform_with_parent_id", None),
            })
        else:
            result = {
                "macrocycle_is_requested": False, 
                "macrocycle_detail": None, 
                "macrocycle_perform_with_parent_id": None, 
                "macrocycle_formatted": None, 
                "macrocycle_other_requests": None
            }
        return {
            "macrocycle_is_requested": result.get("macrocycle_is_requested", False), 
            "macrocycle_detail": result.get("macrocycle_detail", None), 
            "macrocycle_perform_with_parent_id": result.get("macrocycle_perform_with_parent_id", None), 
            "macrocycle_formatted": result.get("macrocycle_formatted", None), 
            "macrocycle_other_requests": result.get("other_requests", None)
        }