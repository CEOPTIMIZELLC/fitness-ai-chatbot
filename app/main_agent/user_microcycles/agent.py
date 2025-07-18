from config import verbose_subagent_steps
from datetime import timedelta

from app import db
from app.models import User_Microcycles, User_Mesocycles
from app.utils.common_table_queries import current_mesocycle, current_microcycle

from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agent import BaseAgent
from app.main_agent.impact_goal_models import MesocycleGoal
from app.main_agent.prompts import mesocycle_system_prompt
from app.main_agent.user_mesocycles import create_mesocycle_agent

from .schedule_printer import MicrocycleSchedulePrinter

# ----------------------------------------- User Microcycles -----------------------------------------

class AgentState(MainAgentState):
    user_mesocycle: dict
    mesocycle_id: int
    microcycle_count: int
    microcycle_duration: any
    start_date: any

class SubAgent(BaseAgent):
    focus = "microcycle"
    parent = "mesocycle"
    sub_agent_title = "Microcycle"
    parent_title = "Mesocycle"
    parent_system_prompt = mesocycle_system_prompt
    parent_goal = MesocycleGoal
    parent_scheduler_agent = create_mesocycle_agent()
    schedule_printer_class = MicrocycleSchedulePrinter

    # Retrieve the Microcycles belonging to the Mesocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.microcycles

    def user_list_query(user_id):
        return User_Microcycles.query.join(User_Mesocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_microcycle(user_id)

    def parent_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Information for Microcycle Scheduling---------")
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
        if verbose_subagent_steps:
            print(f"\t---------Perform Microcycle Scheduling---------")
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
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)