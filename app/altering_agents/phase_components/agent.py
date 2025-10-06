from logging_config import LogAlteringAgent

from app import db
from app.models import User_Workout_Components, User_Workout_Days
from app.common_table_queries.microcycles import currently_active_item as current_microcycle


from app.agent_states.phase_components import AgentState
from app.schedule_printers.phase_components import PhaseComponentSchedulePrinter

from app.altering_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.solver_agents.phase_components import Main as phase_component_main

from .actions import (
    retrieve_parameters, 
    retrieve_weekday_availability_information_from_availability, 
    duration_to_weekdays, 
    workout_day_entry_construction 
)

# ----------------------------------------- User Workout Days -----------------------------------------

class AlteringAgent(BaseAgent):
    focus = "phase_component"
    parent = "microcycle"
    sub_agent_title = "Phase Component"
    schedule_printer_class = PhaseComponentSchedulePrinter()

    # Retrieve the Workout Days belonging to the Microcycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.workout_days

    def parent_retriever_agent(self, user_id):
        return current_microcycle(user_id)

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Retrieving Information for Workout Day Scheduling---------")
        user_microcycle = state["user_microcycle"]
        user_availability = state["user_availability"]
        microcycle_id = user_microcycle["id"]
        phase_id = user_microcycle["phase_id"]
        duration = user_microcycle["duration_days"]
        start_date = user_microcycle["start_date"]

        microcycle_weekdays = duration_to_weekdays(duration, start_date)
        weekday_availability, number_of_available_weekdays, total_availability = retrieve_weekday_availability_information_from_availability(user_availability)

        return {
            "microcycle_id": microcycle_id,
            "phase_id": phase_id,
            "duration": duration,
            "start_date": start_date,
            "microcycle_weekdays": microcycle_weekdays,
            "weekday_availability": weekday_availability,
            "number_of_available_weekdays": number_of_available_weekdays,
            "total_availability": total_availability
        }

    # Query to delete all old workout days belonging to the current microcycle.
    def delete_children_query(self, parent_id):
        db.session.query(User_Workout_Days).filter_by(microcycle_id=parent_id).delete()
        db.session.commit()

    # Executes the agent to create the phase component schedule for each workout in the current microcycle.
    def perform_scheduler(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Perform Workout Day Scheduling---------")
        user_id = state["user_id"]
        phase_id = state["phase_id"]
        microcycle_weekdays = state["microcycle_weekdays"]
        weekday_availability = state["weekday_availability"]
        number_of_available_weekdays = state["number_of_available_weekdays"]
        total_availability = state["total_availability"]

        parameters=retrieve_parameters(user_id, phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability)
        constraints={}

        result = phase_component_main(parameters, constraints)
        return {
            "agent_output": result["output"],
            "schedule_printed": result["formatted"]
        }


    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Convert schedule to SQLAlchemy models.---------")
        phase_components_output = state["agent_output"]
        user_microcycle = state["user_microcycle"]
        microcycle_id = user_microcycle["id"]
        start_date = user_microcycle["start_date"]

        microcycle_weekdays = state["microcycle_weekdays"]
        user_workdays = workout_day_entry_construction(microcycle_weekdays, start_date, microcycle_id)

        for phase_component in phase_components_output:
            # Create a new component entry.
            new_component = User_Workout_Components(
                phase_component_id = phase_component["phase_component_id"],
                bodypart_id = phase_component["bodypart_id"],
                duration = phase_component["duration_var"]
            )

            # Append the component to its corresponding workday.
            user_workdays[phase_component["workday_index"]].workout_components.append(new_component)

        db.session.add_all(user_workdays)
        db.session.commit()
        return {}

# Create main agent.
def create_main_agent_graph():
    agent = AlteringAgent()
    return agent.create_main_agent_graph(AgentState)