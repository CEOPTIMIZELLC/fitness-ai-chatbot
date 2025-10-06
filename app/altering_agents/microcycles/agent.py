from logging_config import LogAlteringAgent
from datetime import timedelta

# Database imports.
from app import db
from app.models import User_Microcycles
from app.common_table_queries.mesocycles import currently_active_item as current_mesocycle

# Agent construction imports.
from app.altering_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.agent_states.microcycles import AgentState
from app.schedule_printers.microcycles import MicrocycleSchedulePrinter

# ----------------------------------------- User Microcycles -----------------------------------------

class AlteringAgent(BaseAgent):
    focus = "microcycle"
    parent = "mesocycle"
    sub_agent_title = "Microcycle"
    schedule_printer_class = MicrocycleSchedulePrinter()

    # Retrieve the Microcycles belonging to the Mesocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.microcycles

    def parent_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Retrieving Information for Microcycle Scheduling---------")
        user_mesocycle = state["user_mesocycle"]

        # Each microcycle must last 1 week.
        microcycle_duration = timedelta(weeks=1)

        # Find how many one week microcycles will be present in the mesocycle
        microcycle_count = user_mesocycle["duration_days"] // microcycle_duration.days
        microcycle_start = user_mesocycle["start_date"]

        return {
            "mesocycle_id": user_mesocycle["id"],
            "microcycle_duration": microcycle_duration,
            "microcycle_count": microcycle_count,
            "start_date": microcycle_start
        }

    # Query to delete all old microcycles belonging to the current mesocycle.
    def delete_children_query(self, parent_id):
        db.session.query(User_Microcycles).filter_by(mesocycle_id=parent_id).delete()
        db.session.commit()

    # Initializes the microcycle schedule for the current mesocycle.
    def perform_scheduler(self, state: AgentState):
        return {}

    # Initializes the microcycle schedule for the current mesocycle.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Perform Microcycle Scheduling---------")
        mesocycle_id = state["mesocycle_id"]
        microcycle_duration = state["microcycle_duration"]
        microcycle_count = state["microcycle_count"]
        microcycle_start = state["start_date"]

        # Create a microcycle for each week in the mesocycle.
        microcycles = []
        for i in range(microcycle_count):
            microcycle_end = microcycle_start + microcycle_duration
            new_microcycle = User_Microcycles(
                mesocycle_id = mesocycle_id,
                order = i+1,
                start_date = microcycle_start,
                end_date = microcycle_end,
            )

            microcycles.append(new_microcycle)

            # Shift the start of the next microcycle to be the end of the current.
            microcycle_start = microcycle_end

        db.session.add_all(microcycles)
        db.session.commit()

        return {}

# Create main agent.
def create_main_agent_graph():
    agent = AlteringAgent()
    return agent.create_main_agent_graph(AgentState)