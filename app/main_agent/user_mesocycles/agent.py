from config import verbose, verbose_subagent_steps
from datetime import timedelta

from app import db
from app.models import User_Mesocycles, User_Macrocycles
from app.agents.phases import Main as phase_main
from app.utils.common_table_queries import current_macrocycle, current_mesocycle

from app.main_agent.user_macrocycles import MacrocycleAgentNode
from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.with_parents import BaseAgent
from app.main_agent.impact_goal_models import MacrocycleGoal
from app.main_agent.prompts import macrocycle_system_prompt
from app.main_agent.utils import construct_phases_list

from .schedule_printer import SchedulePrinter

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class AgentState(MainAgentState):
    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int
    start_date: any
    macrocycle_allowed_weeks: int
    possible_phases: list
    agent_output: list

class SubAgent(MacrocycleAgentNode, BaseAgent, SchedulePrinter):
    focus = "mesocycle"
    parent = "macrocycle"
    sub_agent_title = "Mesocycle"
    parent_title = "Macrocycle"
    parent_system_prompt = macrocycle_system_prompt
    parent_goal = MacrocycleGoal
    parent_scheduler_agent = MacrocycleAgentNode.macrocycle_node

    # Retrieve the Mesocycles belonging to the Macrocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.mesocycles

    def user_list_query(user_id):
        return User_Mesocycles.query.join(User_Macrocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

    def parent_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    # Items extracted from the goal classifier
    def goal_classifier_parser(self, parent_names, goal_class):
        return {
            parent_names["impact"]: goal_class.is_requested,
            parent_names["message"]: goal_class.detail, 
            "macrocycle_alter_old": goal_class.alter_old
        }

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Information for Mesocycle Scheduling---------")
        user_macrocycle = state["user_macrocycle"]
        macrocycle_id = user_macrocycle["id"]
        goal_id = user_macrocycle["goal_id"]
        start_date = user_macrocycle["start_date"]
        macrocycle_allowed_weeks = macrocycle_weeks
        possible_phases = construct_phases_list(int(goal_id))
        return {
            "macrocycle_id": macrocycle_id,
            "goal_id": goal_id,
            "start_date": start_date,
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
            "possible_phases": possible_phases
        }

    # Query to delete all old mesocycles belonging to the current macrocycle.
    def delete_children_query(self, parent_id):
        db.session.query(User_Mesocycles).filter_by(macrocycle_id=parent_id).delete()
        db.session.commit()

    # Executes the agent to create the mesocycle/phase schedule for the current macrocycle.
    def perform_scheduler(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Perform Mesocycle Scheduling---------")
        goal_id = state["goal_id"]
        macrocycle_allowed_weeks = state["macrocycle_allowed_weeks"]
        parameters={
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
            "goal_type": goal_id}
        constraints={}

        # Retrieve all possible phases that can be selected and convert them into a list form.
        parameters["possible_phases"] = construct_phases_list(int(goal_id))

        result = phase_main(parameters, constraints)

        if verbose:
            print(result["formatted"])
        return {
            "agent_output": result["output"]
        }

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Convert schedule to SQLAlchemy models.---------")
        phases_output = state["agent_output"]
        macrocycle_id = state["macrocycle_id"]
        mesocycle_start_date = state["start_date"]

        # Convert output to form that may be stored.
        user_phases = []
        for i, phase in enumerate(phases_output, start=1):
            new_phase = User_Mesocycles(
                macrocycle_id = macrocycle_id,
                phase_id = phase["id"],
                is_goal_phase = phase["is_goal_phase"],
                order = i,
                start_date = mesocycle_start_date,
                end_date = mesocycle_start_date + timedelta(weeks=phase["duration"])
            )

            user_phases.append(new_phase)

            # Set startdate of next phase to be at the end of the current one.
            mesocycle_start_date +=timedelta(weeks=phase["duration"])

        db.session.add_all(user_phases)
        db.session.commit()
        return {}

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)