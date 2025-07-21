from typing_extensions import TypeVar
from app.main_agent.main_agent_state import MainAgentState

from .agent import create_main_agent_graph

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class AgentNode():
    def macrocycle_node(self, state: TState):
        print(f"\n=========Starting User Macrocycle=========")
        if state["macrocycle_impacted"]:
            goal_agent = create_main_agent_graph()
            result = goal_agent.invoke({
                "user_id": state["user_id"], 
                "user_input": state["user_input"], 
                "attempts": state["attempts"], 
                "macrocycle_impacted": state["macrocycle_impacted"], 
                "macrocycle_is_altered": state["macrocycle_is_altered"], 
                "macrocycle_message": state["macrocycle_message"],
                "macrocycle_alter_old": state["macrocycle_alter_old"]
            })
        else:
            result = {
                "macrocycle_impacted": False, 
                "macrocycle_is_altered": False, 
                "macrocycle_message": None, 
                "macrocycle_formatted": None, 
                "macrocycle_alter_old": False
            }
        return {
            "macrocycle_impacted": result["macrocycle_impacted"], 
            "macrocycle_is_altered": result["macrocycle_is_altered"], 
            "macrocycle_message": result["macrocycle_message"], 
            "macrocycle_formatted": result["macrocycle_formatted"], 
            "macrocycle_alter_old": result["macrocycle_alter_old"]
        }