from logging_config import LogMainSubAgent

from langgraph.graph import StateGraph, START, END

from app import db
from app.agents.phase_components import Main as phase_component_main
from app.models import (
    User_Workout_Components, 
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days
)

from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles
from app.utils.common_table_queries import current_microcycle, current_workout_day

from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.with_availability import BaseAgentWithAvailability as BaseAgent
from app.main_agent.user_microcycles import create_microcycle_agent
from app.impact_goal_models import MicrocycleGoal
from app.goal_prompts import microcycle_system_prompt

from .actions import (
    retrieve_parameters, 
    retrieve_availability_for_week, 
    retrieve_weekday_availability_information_from_availability, 
    duration_to_weekdays, 
    workout_day_entry_construction 
)
from app.schedule_printers import PhaseComponentSchedulePrinter

# ----------------------------------------- User Workout Days -----------------------------------------

class AgentState(MainAgentState):
    user_microcycle: dict
    microcycle_id: int
    phase_id: int
    duration: any

    microcycle_weekdays: list
    user_availability: list
    weekday_availability: list
    number_of_available_weekdays: int
    total_availability: int

    start_date: any
    agent_output: list
    schedule_printed: str

class SubAgent(BaseAgent):
    focus = "phase_component"
    parent = "microcycle"
    sub_agent_title = "Phase Component"
    parent_title = "Microcycle"
    parent_system_prompt = microcycle_system_prompt
    parent_goal = MicrocycleGoal
    parent_scheduler_agent = create_microcycle_agent()
    schedule_printer_class = PhaseComponentSchedulePrinter()

    # Retrieve the Workout Days belonging to the Microcycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.workout_days

    def user_list_query(self, user_id):
        return User_Workout_Days.query.join(User_Microcycles).join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    def parent_retriever_agent(self, user_id):
        return current_microcycle(user_id)

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        parent_db_entry = self.parent_retriever_agent(user_id)
        parent_db_entry.mesocycles.phase_id = new_parent_id
        return parent_db_entry

    # Retrieve User's Availability.
    def availability_retriever_agent(self, state: AgentState):
        user_id = state["user_id"]
        user_availability = retrieve_availability_for_week(user_id)

        # Convert to list of dictionaries.
        return {"user_availability": [availability.to_dict() for availability in user_availability]}

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for Workout Day Scheduling---------")
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
        LogMainSubAgent.agent_steps(f"\t---------Perform Workout Day Scheduling---------")
        user_id = state["user_id"]
        phase_id = state["phase_id"]
        microcycle_weekdays = state["microcycle_weekdays"]
        weekday_availability = state["weekday_availability"]
        number_of_available_weekdays = state["number_of_available_weekdays"]
        total_availability = state["total_availability"]

        parameters=retrieve_parameters(user_id, phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability)
        constraints={}

        result = phase_component_main(parameters, constraints)
        LogMainSubAgent.agent_output(result["formatted"])

        return {
            "agent_output": result["output"],
            "schedule_printed": result["formatted"]
        }


    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Convert schedule to SQLAlchemy models.---------")
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
    def _add_impact_pipeline_to_workflow(self, workflow):
        workflow.add_node("retrieve_availability", self.retrieve_availability)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_conditional_edges(
            START,
            self.confirm_impact,
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "retrieve_availability"                       # Retreive the availability for the alteration.
            }
        )
        workflow.add_edge("end_node", END)
        return workflow

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("delete_old_children", self.delete_old_children)

        # Whether the focus element has been indicated to be impacted.
        self._add_impact_pipeline_to_workflow(workflow)

        # Whether an availability for the user exists.
        self._add_availability_retrieval_pipeline_to_workflow(workflow)

        # Retrieve the parent element if an availability is found.
        workflow.add_edge("availability_retrieved", "retrieve_parent")

        # Whether an availability for the user is allowed to be created where one doesn't already exist.
        self._add_availability_permission_pipeline_to_workflow(workflow)
        workflow.add_edge("availability", "retrieve_availability")

        # Whether a parent element exists.
        self._add_parent_retrieval_pipeline_to_workflow(workflow)

        # What to do depending on if the request is to read or write.
        self._add_read_write_pipeline_to_workflow(workflow)

        # Whether a parent element is allowed to be created where one doesn't already exist.
        self._add_parent_permission_pipeline_to_workflow(workflow)

        workflow.add_edge("retrieve_information", "delete_old_children")
        self._add_scheduler_pipeline_to_workflow(workflow)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)