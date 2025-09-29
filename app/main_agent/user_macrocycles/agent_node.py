from logging_config import LogMainSubAgent
from typing_extensions import TypeVar
from app.agent_states.main_agent_state import MainAgentState

from .agent import create_main_agent_graph

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class AgentNode():
    def macrocycle_node(self, state: TState):
        LogMainSubAgent.agent_introductions(f"\n=========Starting User Macrocycle=========")
        if state["macrocycle_is_requested"]:
            goal_agent = create_main_agent_graph()
            result = goal_agent.invoke({
                "user_id": state["user_id"], 
                "user_input": state["user_input"], 
                "attempts": state["attempts"], 
                "macrocycle_is_requested": state["macrocycle_is_requested"], 
                "macrocycle_detail": state["macrocycle_detail"],
                "macrocycle_perform_with_parent_id": state["macrocycle_perform_with_parent_id"] if "macrocycle_perform_with_parent_id" in state else None,
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
            "macrocycle_is_requested": result["macrocycle_is_requested"], 
            "macrocycle_detail": result["macrocycle_detail"], 
            "macrocycle_perform_with_parent_id": result["macrocycle_perform_with_parent_id"] if "macrocycle_perform_with_parent_id" in result else None, 
            "macrocycle_formatted": result["macrocycle_formatted"], 
            "macrocycle_other_requests": result.get("other_requests")
        }