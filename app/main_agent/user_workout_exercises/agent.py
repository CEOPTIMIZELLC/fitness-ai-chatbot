from logging_config import LogMainSubAgent
from flask import abort

from langgraph.graph import StateGraph, START, END

from app import db
from app.models import User_Workout_Exercises, User_Workout_Days
from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

from app.agents.exercises import exercises_main
from app.utils.common_table_queries import current_workout_day

from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.with_availability import BaseAgentWithAvailability as BaseAgent
from app.main_agent.user_workout_days import create_microcycle_scheduler_agent
from app.impact_goal_models import PhaseComponentGoal
from app.goal_prompts import phase_component_system_prompt
from app.edit_agents import create_workout_edit_agent

from .actions import retrieve_availability_for_day, retrieve_parameters
from app.schedule_printers import WorkoutScheduleSchedulePrinter
from app.list_printers import WorkoutScheduleListPrinter

# ----------------------------------------- User Workout Exercises -----------------------------------------

class AgentState(MainAgentState):
    user_phase_component: dict
    phase_component_id: int
    loading_system_id: int

    user_availability: int
    start_date: any
    agent_output: list
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

    include_editor = True

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

    # In between node for chained conditional edges.
    def parent_retrieved(self, state):
        return {}

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
    def _add_read_write_pipeline_to_workflow(self, workflow: StateGraph):
        workflow.add_node("read_operation_is_plural", self.chained_conditional_inbetween)

        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("get_user_list", self.get_user_list)

        # Whether the goal is to read or alter user elements.
        workflow.add_conditional_edges(
            "retrieve_information",
            self.determine_operation,
            {
                "read": "read_operation_is_plural",                     # In between step for if the read operation is plural.
                "alter": "delete_old_children"                          # Delete the old children for the alteration.
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
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        return workflow

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("retrieve_availability", self.retrieve_availability)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("delete_old_children", self.delete_old_children)

        # Whether the focus element has been indicated to be impacted.
        self._add_impact_pipeline_to_workflow(workflow)

        # Whether a parent element exists.
        self._add_parent_retrieval_pipeline_to_workflow(workflow)
        workflow.add_edge("parent_retrieved", "retrieve_availability")

        # Whether a parent element is allowed to be created where one doesn't already exist.
        self._add_parent_permission_pipeline_to_workflow(workflow)

        # Whether an availability for the user exists.
        self._add_availability_retrieval_pipeline_to_workflow(workflow)

        # Retrieve the information for the alteration.
        workflow.add_edge("availability_retrieved", "retrieve_information")

        # Whether an availability for the user is allowed to be created where one doesn't already exist.
        self._add_availability_permission_pipeline_to_workflow(workflow)
        workflow.add_edge("availability", "retrieve_parent")

        # What to do depending on if the request is to read or write.
        self._add_read_write_pipeline_to_workflow(workflow)

        self._add_scheduler_pipeline_to_workflow(workflow)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)