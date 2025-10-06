from logging_config import LogAlteringAgent
from flask import abort

# Database imports.
from app import db
from app.models import User_Workout_Exercises, User_Workout_Days
from app.common_table_queries.phase_components import currently_active_item as current_workout_day

# Agent construction imports.
from app.altering_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.agent_states.workout_schedule import AgentState
from app.schedule_printers.workout_schedule import WorkoutScheduleSchedulePrinter

# Sub agent imports.
from app.edit_agents.workout_schedule import create_editing_agent
from app.solver_agents.exercises import exercises_main

# Local imports.
from .actions import retrieve_parameters

# ----------------------------------------- User Workout Exercises -----------------------------------------

class AlteringAgent(BaseAgent):
    focus = "workout_schedule"
    parent = "phase_component"
    sub_agent_title = "User Workout"
    focus_edit_agent = create_editing_agent()
    schedule_printer_class = WorkoutScheduleSchedulePrinter()
    is_edited = True

    # Retrieve the Exercises belonging to the Workout.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.exercises

    def parent_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Retrieving Information for Workout Exercise Scheduling---------")
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
        LogAlteringAgent.agent_steps(f"\t---------Perform Workout Exercise Scheduling---------")
        user_id = state["user_id"]
        workout_day_id = state["phase_component_id"]
        user_workout_day = db.session.get(User_Workout_Days, workout_day_id)
        loading_system_id = state["loading_system_id"]

        availability = state["user_availability"]

        # Retrieve parameters.
        parameters = retrieve_parameters(user_id, user_workout_day, availability)
        constraints={"vertical_loading": loading_system_id == 1}

        result = exercises_main(parameters, constraints)
        return {"agent_output": result["output"]}

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Convert schedule to SQLAlchemy models.---------")
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
        LogAlteringAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
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
        LogAlteringAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

# Create main agent.
def create_main_agent_graph():
    agent = AlteringAgent()
    return agent.create_main_agent_graph(AgentState)