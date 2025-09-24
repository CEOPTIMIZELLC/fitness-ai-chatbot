from app.utils.common_table_queries import current_mesocycle

from app.main_agent.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.impact_goal_models import MesocycleGoal
from app.goal_prompts import mesocycle_system_prompt
from app.main_agent.user_mesocycles import create_mesocycle_agent

from app.agent_states.microcycles import AgentState

from app.altering_agents.microcycles.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.microcycles.agent import create_main_agent_graph as create_reading_agent

# ----------------------------------------- User Microcycles -----------------------------------------

class SubAgent(BaseAgent):
    focus = "microcycle"
    parent = "mesocycle"
    sub_agent_title = "Microcycle"
    parent_title = "Mesocycle"
    parent_system_prompt = mesocycle_system_prompt
    parent_goal = MesocycleGoal
    parent_scheduler_agent = create_mesocycle_agent()
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

    def parent_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        parent_db_entry = self.parent_retriever_agent(user_id)
        parent_db_entry.phase_id = new_parent_id
        return parent_db_entry

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)