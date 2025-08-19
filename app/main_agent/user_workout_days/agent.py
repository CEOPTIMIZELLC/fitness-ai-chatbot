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

class SubAgent(BaseAgent, PhaseComponentSchedulePrinter):
    focus = "phase_component"
    parent = "microcycle"
    sub_agent_title = "Phase Component"
    parent_title = "Microcycle"
    parent_system_prompt = microcycle_system_prompt
    parent_goal = MicrocycleGoal
    parent_scheduler_agent = create_microcycle_agent()

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
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("retrieve_availability", self.retrieve_availability)
        workflow.add_node("ask_for_availability_permission", self.ask_for_availability_permission)
        workflow.add_node("availability_requests_extraction", self.availability_requests_extraction)
        workflow.add_node("availability_permission_denied", self.availability_permission_denied)
        workflow.add_node("availability", self.availability_node)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("ask_for_permission", self.ask_for_permission)
        workflow.add_node("parent_requests_extraction", self.parent_requests_extraction)
        workflow.add_node("permission_denied", self.permission_denied)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
        workflow.add_node("parent_retrieved", self.parent_retrieved)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("read_operation_is_plural", self.chained_conditional_inbetween)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("perform_scheduler", self.perform_scheduler)
        workflow.add_node("agent_output_to_sqlalchemy_model", self.agent_output_to_sqlalchemy_model)
        workflow.add_node("read_user_current_element", self.read_user_current_element)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("get_user_list", self.get_user_list)
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

        # Whether an availability for the user exists.
        workflow.add_conditional_edges(
            "retrieve_availability",
            self.confirm_availability,
            {
                "no_availability": "ask_for_availability_permission",   # No parent element exists.
                "availability": "retrieve_parent"                       # Retrieve the parent element if an availability is found.
            }
        )

        # Whether an availability for the user is allowed to be created where one doesn't already exist.
        workflow.add_edge("ask_for_availability_permission", "availability_requests_extraction")
        workflow.add_conditional_edges(
            "availability_requests_extraction",
            self.confirm_availability_permission,
            {
                "permission_denied": "availability_permission_denied",  # The agent isn't allowed to create availability.
                "permission_granted": "availability"                    # The agent is allowed to create availability.
            }
        )
        workflow.add_edge("availability", "retrieve_availability")

        # Whether a parent element exists.
        workflow.add_conditional_edges(
            "retrieve_parent",
            self.confirm_parent,
            {
                "no_parent": "ask_for_permission",                      # No parent element exists.
                "parent": "parent_retrieved"                            # In between step for if a parent element exists.
            }
        )

        # Whether the goal is to read or alter user elements.
        workflow.add_conditional_edges(
            "parent_retrieved",
            self.determine_operation,
            {
                "read": "operation_is_read",                            # In between step for if the operation is read.
                "alter": "retrieve_information"                         # Retrieve the information for the alteration.
            }
        )

        # Whether the read operations is for a single element or plural elements.
        workflow.add_conditional_edges(
            "operation_is_read",
            self.determine_read_operation,
            {
                "plural": "read_operation_is_plural",                   # In between step for if the read operation is plural.
                "singular": "read_user_current_element"                 # Read the current element.
            }
        )

        # Whether the plural list is for all of the elements or all elements belonging to the user.
        workflow.add_conditional_edges(
            "read_operation_is_plural",
            self.determine_read_filter_operation,
            {
                "current": "get_formatted_list",                        # Read the current schedule.
                "all": "get_user_list"                                  # Read all user elements.
            }
        )

        # Whether a parent element is allowed to be created where one doesn't already exist.
        workflow.add_edge("ask_for_permission", "parent_requests_extraction")
        workflow.add_conditional_edges(
            "parent_requests_extraction",
            self.confirm_permission,
            {
                "permission_denied": "permission_denied",               # The agent isn't allowed to create a parent.
                "permission_granted": "parent_agent"                    # The agent is allowed to create a parent.
            }
        )
        workflow.add_edge("parent_agent", "retrieve_parent")

        workflow.add_edge("retrieve_information", "delete_old_children")
        workflow.add_edge("delete_old_children", "perform_scheduler")
        workflow.add_edge("perform_scheduler", "agent_output_to_sqlalchemy_model")
        workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
        workflow.add_edge("permission_denied", "end_node")
        workflow.add_edge("availability_permission_denied", "end_node")
        workflow.add_edge("read_user_current_element", "end_node")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)