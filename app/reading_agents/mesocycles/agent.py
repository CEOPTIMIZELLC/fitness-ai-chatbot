from app.models import User_Mesocycles, User_Macrocycles
from app.common_table_queries.macrocycles import currently_active_item as current_macrocycle
from app.common_table_queries.mesocycles import currently_active_item as current_mesocycle

from app.reading_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.schedule_printers.mesocycles import MesocycleSchedulePrinter

from app.agent_states.mesocycles import AgentState

# ----------------------------------------- User Mesocycles -----------------------------------------

class SubAgent(BaseAgent):
    focus = "mesocycle"
    parent = "macrocycle"
    sub_agent_title = "Mesocycle"
    schedule_printer_class = MesocycleSchedulePrinter()

    def user_list_query(self, user_id):
        return User_Mesocycles.query.join(User_Macrocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

    # Retrieve the Mesocycles belonging to the Macrocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.mesocycles

    def parent_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)