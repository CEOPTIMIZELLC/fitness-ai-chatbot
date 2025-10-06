from app.models import Weekday_Library, User_Weekday_Availability
from app.common_table_queries.microcycles import currently_active_item as current_microcycle


from app.parent_retriever_agents.base_sub_agents.base import BaseAgent
from app.main_agent.user_microcycles import create_microcycle_agent
from app.impact_goal_models.microcycles import MicrocycleGoal
from app.goal_prompts.microcycles import microcycle_system_prompt

from app.agent_states.phase_components import AgentState

# ----------------------------------------- User Workout Days -----------------------------------------

class SubAgent(BaseAgent):
    focus = "phase_component"
    parent = "microcycle"
    sub_agent_title = "Phase Component"
    parent_title = "Microcycle"
    parent_system_prompt = microcycle_system_prompt
    parent_goal = MicrocycleGoal
    parent_scheduler_agent = create_microcycle_agent()

    def parent_retriever_agent(self, user_id):
        return current_microcycle(user_id)

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        parent_db_entry = self.parent_retriever_agent(user_id)
        parent_db_entry.mesocycles.phase_id = new_parent_id
        return parent_db_entry

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)