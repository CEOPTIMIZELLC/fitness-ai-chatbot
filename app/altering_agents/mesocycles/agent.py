from logging_config import LogAlteringAgent
from datetime import timedelta

from app import db
from app.models import User_Mesocycles
from app.utils.common_table_queries import current_macrocycle

from app.main_agent.utils import construct_phases_list

from app.agent_states.mesocycles import AgentState
from app.schedule_printers.mesocycles import MesocycleSchedulePrinter

from app.altering_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.edit_agents.mesocycles import create_main_agent_graph as create_mesocycle_edit_agent
from app.solver_agents.phases import Main as phase_main

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class AlteringAgent(BaseAgent):
    focus = "mesocycle"
    parent = "macrocycle"
    sub_agent_title = "Mesocycle"
    focus_edit_agent = create_mesocycle_edit_agent()
    schedule_printer_class = MesocycleSchedulePrinter()
    is_edited = True

    # Retrieve the Mesocycles belonging to the Macrocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.mesocycles

    def parent_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Retrieving Information for Mesocycle Scheduling---------")
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
        LogAlteringAgent.agent_steps(f"\t---------Perform Mesocycle Scheduling---------")
        goal_id = state["goal_id"]
        macrocycle_allowed_weeks = state["macrocycle_allowed_weeks"]
        parameters={
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
            "goal_type": goal_id}
        constraints={}

        # Retrieve all possible phases that can be selected and convert them into a list form.
        parameters["possible_phases"] = construct_phases_list(int(goal_id))

        result = phase_main(parameters, constraints)
        LogAlteringAgent.agent_output(result["formatted"])

        agent_output = result["output"]
        mesocycle_start_date = state["start_date"]

        # Add the startdates and enddates to the schedule items.
        for i, schedule_item in enumerate(agent_output, start=1):
            phase_duration = schedule_item["duration"]
            schedule_item["start_date"] = mesocycle_start_date
            schedule_item["end_date"] = mesocycle_start_date + timedelta(weeks=phase_duration)
            schedule_item["order"] = i

            # Set startdate of next phase to be at the end of the current one.
            mesocycle_start_date +=timedelta(weeks=phase_duration)

        return {
            "agent_output": agent_output,
            "schedule_printed": result["formatted"]
        }

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Convert schedule to SQLAlchemy models.---------")
        phases_output = state["agent_output"]
        macrocycle_id = state["macrocycle_id"]

        # Convert output to form that may be stored.
        user_phases = []
        for phase in phases_output:
            new_phase = User_Mesocycles(
                macrocycle_id = macrocycle_id,
                phase_id = phase["id"],
                is_goal_phase = phase["is_goal_phase"],
                order = phase["order"],
                start_date = phase["start_date"],
                end_date = phase["end_date"]
            )

            user_phases.append(new_phase)

        db.session.add_all(user_phases)
        db.session.commit()
        return {}

# Create main agent.
def create_main_agent_graph():
    agent = AlteringAgent()
    return agent.create_main_agent_graph(AgentState)