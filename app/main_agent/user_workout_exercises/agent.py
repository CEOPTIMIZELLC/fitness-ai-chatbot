from logging_config import LogMainSubAgent
from flask import abort

from langgraph.graph import StateGraph, START, END

from app import db
from app.models import User_Workout_Exercises, User_Workout_Days
from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

from app.solver_agents.exercises import exercises_main
from app.utils.common_table_queries import current_workout_day

from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.with_availability import BaseAgentWithAvailability as BaseAgent
from app.main_agent.base_sub_agents.base import confirm_impact, determine_if_alter, determine_if_read, determine_read_filter_operation, confirm_regenerate
from app.main_agent.base_sub_agents.with_parents import confirm_parent, confirm_permission
from app.main_agent.base_sub_agents.with_availability import confirm_availability, confirm_availability_permission
from app.main_agent.user_workout_days import create_microcycle_scheduler_agent
from app.impact_goal_models import PhaseComponentGoal
from app.goal_prompts import phase_component_system_prompt
from app.edit_agents import create_workout_edit_agent

from .actions import retrieve_availability_for_day, retrieve_parameters
from app.schedule_printers import WorkoutScheduleSchedulePrinter
from app.schedule_printers import WorkoutScheduleListPrinter

# ----------------------------------------- User Workout Exercises -----------------------------------------

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    user_phase_component: dict
    phase_component_id: int
    loading_system_id: int

    user_availability: int
    start_date: any
    agent_output: list
    should_regenerate: bool
    schedule_printed: str

class SubAgent(BaseAgent):
    focus = "workout_schedule"
    parent = "phase_component"
    sub_agent_title = "User Workout"
    parent_title = "Phase Component"
    parent_system_prompt = phase_component_system_prompt
    parent_goal = PhaseComponentGoal
    parent_scheduler_agent = create_microcycle_scheduler_agent()
    focus_edit_agent = create_workout_edit_agent()
    schedule_printer_class = WorkoutScheduleSchedulePrinter()
    list_printer_class = WorkoutScheduleListPrinter()

    # Retrieve the Exercises belonging to the Workout.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.exercises

    def user_list_query(self, user_id):
        return (
            User_Workout_Exercises.query
            .join(User_Workout_Days)
            .join(User_Microcycles)
            .join(User_Mesocycles)
            .join(User_Macrocycles)
            .filter_by(user_id=user_id)
            .all())

    def focus_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    def parent_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    # Retrieve User's Availability.
    def availability_retriever_agent(self, state: AgentState):
        user_id = state["user_id"]
        user_workout_day = state["user_phase_component"]
        return {"user_availability": retrieve_availability_for_day(user_id, user_workout_day["weekday_id"])}


    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for Workout Exercise Scheduling---------")
        user_workout_day = state["user_phase_component"]

        return {
            "phase_component_id": user_workout_day["id"],
            "loading_system_id": user_workout_day["loading_system_id"]
        }

    # Query to delete all old exercises belonging to the current workout.
    def delete_children_query(self, parent_id):
        db.session.query(User_Workout_Exercises).filter_by(workout_day_id=parent_id).delete()
        db.session.commit()

    # Executes the agent to create the phase component schedule for each workout in the current workout_day.
    def perform_scheduler(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Perform Workout Exercise Scheduling---------")
        user_id = state["user_id"]
        workout_day_id = state["phase_component_id"]
        user_workout_day = db.session.get(User_Workout_Days, workout_day_id)
        loading_system_id = state["loading_system_id"]

        availability = state["user_availability"]

        # Retrieve parameters.
        parameters = retrieve_parameters(user_id, user_workout_day, availability)
        constraints={"vertical_loading": loading_system_id == 1}

        result = exercises_main(parameters, constraints)
        LogMainSubAgent.agent_output(result["formatted"])

        return {"agent_output": result["output"]}

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Convert schedule to SQLAlchemy models.---------")
        workout_day_id = state["phase_component_id"]
        exercises_output = state["agent_output"]

        user_workout_exercises = []
        for i, exercise in enumerate(exercises_output, start=1):
            # Create a new exercise entry.
            new_exercise = User_Workout_Exercises(
                workout_day_id = workout_day_id,
                phase_component_id = exercise["phase_component_id"],
                exercise_id = exercise["exercise_id"],
                bodypart_id = exercise["bodypart_id"],
                order = i,
                reps = exercise["reps"],
                sets = exercise["sets"],
                intensity = exercise["intensity"],
                rest = exercise["rest"],
                weight = exercise["weight"],
                true_exercise_flag = exercise["true_exercise_flag"]
            )

            user_workout_exercises.append(new_exercise)

        db.session.add_all(user_workout_exercises)
        db.session.commit()
        return {}

    # Print output.
    def get_formatted_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        workout_day_id = state["phase_component_id"]
        parent_db_entry = db.session.get(User_Workout_Days, workout_day_id)
        workout_date = str(parent_db_entry.date)

        schedule_from_db = self.retrieve_children_entries_from_parent(parent_db_entry)
        if not schedule_from_db:
            abort(404, description=f"No {self.focus}s found for the {self.parent}.")
        
        loading_system_id = state["loading_system_id"]

        user_workout_exercises_dict = [user_workout_exercise.to_dict() | 
                                    {"component_id": user_workout_exercise.phase_components.components.id}
                                    for user_workout_exercise in schedule_from_db]

        formatted_schedule = self.schedule_printer_class.run_printer(workout_date, loading_system_id, user_workout_exercises_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}


    # Print output.
    def get_user_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_id = state["user_id"]

        schedule_from_db = self.user_list_query(user_id)
        if not schedule_from_db:
            abort(404, description=f"No {self.focus}s found for the user.")

        user_workout_exercises_dict = [user_workout_exercise.to_dict() | 
                                    {"component_id": user_workout_exercise.phase_components.components.id}
                                    for user_workout_exercise in schedule_from_db]

        formatted_schedule = self.list_printer_class.run_printer(user_workout_exercises_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("ask_for_permission", self.ask_for_permission)
        workflow.add_node("parent_requests_extraction", self.parent_requests_extraction)
        workflow.add_node("permission_denied", self.permission_denied)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
        workflow.add_node("parent_retrieved", self.chained_conditional_inbetween)
        workflow.add_node("retrieve_availability", self.retrieve_availability)
        workflow.add_node("ask_for_availability_permission", self.ask_for_availability_permission)
        workflow.add_node("availability_requests_extraction", self.availability_requests_extraction)
        workflow.add_node("availability_permission_denied", self.availability_permission_denied)
        workflow.add_node("availability", self.availability_node)
        workflow.add_node("read_operation_is_plural", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("perform_scheduler", self.perform_scheduler)
        workflow.add_node("editor_agent", self.focus_edit_agent)
        workflow.add_node("agent_output_to_sqlalchemy_model", self.agent_output_to_sqlalchemy_model)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            confirm_impact, 
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "retrieve_parent"                             # Retrieve the parent element if an impact is indicated.
            }
        )

        # Whether a parent element exists.
        workflow.add_conditional_edges(
            "retrieve_parent",
            confirm_parent, 
            {
                "no_parent": "ask_for_permission",                      # No parent element exists.
                "parent": "parent_retrieved"                            # In between step for if a parent element exists.
            }
        )
        workflow.add_edge("parent_retrieved", "retrieve_availability")


        # Whether a parent element is allowed to be created where one doesn't already exist.
        workflow.add_edge("ask_for_permission", "parent_requests_extraction")
        workflow.add_conditional_edges(
            "parent_requests_extraction",
            confirm_permission, 
            {
                "permission_denied": "permission_denied",               # The agent isn't allowed to create a parent.
                "permission_granted": "parent_agent"                    # The agent is allowed to create a parent.
            }
        )
        workflow.add_edge("parent_agent", "retrieve_parent")

        # Whether an availability for the user exists.
        workflow.add_conditional_edges(
            "retrieve_availability",
            confirm_availability, 
            {
                "no_availability": "ask_for_availability_permission",   # No parent element exists.
                "availability": "retrieve_information"                  # Retrieve the information for the alteration.
            }
        )

        # Whether an availability for the user is allowed to be created where one doesn't already exist.
        workflow.add_edge("ask_for_availability_permission", "availability_requests_extraction")
        workflow.add_conditional_edges(
            "availability_requests_extraction",
            confirm_availability_permission, 
            {
                "permission_denied": "availability_permission_denied",  # The agent isn't allowed to create availability.
                "permission_granted": "availability"                    # The agent is allowed to create availability.
            }
        )
        workflow.add_edge("availability", "retrieve_parent")

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "retrieve_information",
            determine_if_alter, 
            {
                "not_alter": "operation_is_not_alter",                  # In between step for if the operation is not alter.
                "alter": "delete_old_children"                          # Delete the old children for the alteration.
            }
        )

        # Whether the goal is to read user elements.
        workflow.add_conditional_edges(
            "operation_is_not_alter",
            determine_if_read, 
            {
                "not_read": "end_node",                                 # End subagent if nothing is requested.
                "read": "read_operation_is_plural"                      # In between step for if the read operation is plural.
            }
        )
        # Whether the plural list is for all of the elements or all elements belonging to the user.
        workflow.add_conditional_edges(
            "read_operation_is_plural",
            determine_read_filter_operation, 
            {
                "current": "get_formatted_list",                        # Read the current schedule.
                "all": "get_user_list"                                  # Read all user elements.
            }
        )

        workflow.add_edge("delete_old_children", "perform_scheduler")
        workflow.add_edge("perform_scheduler", "editor_agent")

        # Whether the scheduler should be performed again.
        workflow.add_conditional_edges(
            "editor_agent",
            confirm_regenerate, 
            {
                "is_regenerated": "perform_scheduler",                  # Perform the scheduler again if regenerating.
                "not_regenerated": "agent_output_to_sqlalchemy_model"   # The agent should move on to adding the information to the database.
            }
        )

        workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
        workflow.add_edge("permission_denied", "end_node")
        workflow.add_edge("availability_permission_denied", "end_node")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)