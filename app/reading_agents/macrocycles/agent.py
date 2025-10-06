# Database imports.
from app.models import User_Macrocycles
from app.common_table_queries.macrocycles import currently_active_item as current_macrocycle

# Agent construction imports.
from app.reading_agents.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.agent_states.macrocycles import AgentState
from app.schedule_printers.macrocycles import MacrocycleSchedulePrinter

# ----------------------------------------- User Macrocycles -----------------------------------------

class SubAgent(BaseAgent):
    focus = "macrocycle"
    sub_agent_title = "Macrocycle"
    schedule_printer_class = MacrocycleSchedulePrinter()

    def user_list_query(self, user_id):
        return User_Macrocycles.query.filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    def focus_list_retriever_agent(self, user_id):
        return [current_macrocycle(user_id)]

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)