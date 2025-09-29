from app.db_session import session_scope
from app.models import User_Macrocycles

from app.main_agent.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.impact_goal_models.macrocycles import MacrocycleGoal
from app.goal_prompts.macrocycles import macrocycle_system_prompt

from app.agent_states.macrocycles import AgentState

from app.altering_agents.macrocycles.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.macrocycles.agent import create_main_agent_graph as create_reading_agent

# ----------------------------------------- User Macrocycles -----------------------------------------

class SubAgent(BaseAgent):
    focus = "macrocycle"
    sub_agent_title = "Macrocycle"
    focus_system_prompt = macrocycle_system_prompt
    focus_goal = MacrocycleGoal
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

    # Performs necessary formatting changes for the subagent before changing the state.
    def format_operations(self, state_updates):
        # Combine the alter and creation requests since they are synonamous for availability.
        if any(key in state_updates for key in ("is_alter", "is_create")):
            is_alter = state_updates.pop("is_alter", False) or state_updates.pop("is_create", False)
            
            # Combine requests.
            item_request_list = [state_updates.pop("alter_detail", None), state_updates.pop("create_detail", None)]
            alter_detail = " ".join(
                value
                for value in item_request_list
                if value != None
            )

            state_updates["is_alter"] = is_alter
            state_updates["alter_detail"] = alter_detail
        return state_updates

    # Creates the new macrocycle of the determined type.
    def create_new_macrocycle(self, state: AgentState):
        user_id = state["user_id"]
        goal_id = state["goal_id"]
        new_goal = state["macrocycle_detail"]
        payload = {}
        with session_scope() as s:
            user_macrocycle = User_Macrocycles(user_id=user_id, goal_id=goal_id, goal=new_goal)
            s.add(user_macrocycle)

            # get PKs without committing the transaction
            s.flush()

            # load defaults/server-side values
            s.refresh(user_macrocycle)
            payload = user_macrocycle.to_dict()

        return {"user_macrocycle": payload}

    # Alters the current macrocycle to be the determined type.
    def alter_old_macrocycle(self, state: AgentState):
        goal_id = state["goal_id"]
        new_goal = state["macrocycle_detail"]
        macrocycle_id = state["macrocycle_id"]
        payload = {}
        with session_scope() as s:
            user_macrocycle = s.get(User_Macrocycles, macrocycle_id)
            user_macrocycle.goal = new_goal
            user_macrocycle.goal_id = goal_id

            # get PKs without committing the transaction
            s.flush()

            # load defaults/server-side values
            s.refresh(user_macrocycle)
            payload = user_macrocycle.to_dict()

        return {"user_macrocycle": payload}

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)