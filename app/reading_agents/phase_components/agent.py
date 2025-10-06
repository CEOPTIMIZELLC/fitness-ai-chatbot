from app.models import (
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days
)

from app.common_table_queries.microcycles import currently_active_item as current_microcycle
from app.common_table_queries.phase_components import currently_active_item as current_workout_day

from app.reading_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.schedule_printers.phase_components import PhaseComponentSchedulePrinter

from app.agent_states.phase_components import AgentState

# ----------------------------------------- User Workout Days -----------------------------------------

class SubAgent(BaseAgent):
    focus = "phase_component"
    parent = "microcycle"
    sub_agent_title = "Phase Component"
    schedule_printer_class = PhaseComponentSchedulePrinter()

    def user_list_query(self, user_id):
        return User_Workout_Days.query.join(User_Microcycles).join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    # Retrieve the Workout Days belonging to the Microcycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.workout_days

    def parent_retriever_agent(self, user_id):
        return current_microcycle(user_id)

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)