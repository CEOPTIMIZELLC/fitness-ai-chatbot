from app.models import User_Microcycles, User_Mesocycles, User_Macrocycles
from app.common_table_queries.mesocycles import currently_active_item as current_mesocycle
from app.common_table_queries.microcycles import currently_active_item as current_microcycle

from app.reading_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.schedule_printers.microcycles import MicrocycleSchedulePrinter

from app.agent_states.microcycles import AgentState

# ----------------------------------------- User Microcycles -----------------------------------------

class SubAgent(BaseAgent):
    focus = "microcycle"
    parent = "mesocycle"
    sub_agent_title = "Microcycle"
    schedule_printer_class = MicrocycleSchedulePrinter()

    def user_list_query(self, user_id):
        return User_Microcycles.query.join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_microcycle(user_id)

    # Retrieve the Microcycles belonging to the Mesocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.microcycles

    def parent_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)