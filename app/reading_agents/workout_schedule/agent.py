from logging_config import LogReadingAgent

from flask import abort

from langgraph.graph import StateGraph, START, END

# Database imports.
from app import db
from app.models import User_Workout_Exercises, User_Workout_Days
from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles
from app.common_table_queries.phase_components import currently_active_item as current_workout_day

# Agent construction imports.
from app.reading_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.reading_agents.base_sub_agents.base import determine_read_filter_operation
from app.agent_states.workout_schedule import AgentState
from app.schedule_printers.workout_schedule import WorkoutScheduleSchedulePrinter
from app.schedule_printers.workout_schedule import WorkoutScheduleListPrinter

# ----------------------------------------- User Workout Exercises -----------------------------------------

class SubAgent(BaseAgent):
    focus = "workout_schedule"
    parent = "phase_component"
    sub_agent_title = "User Workout"
    schedule_printer_class = WorkoutScheduleSchedulePrinter()
    list_printer_class = WorkoutScheduleListPrinter()

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

    # Retrieve the Exercises belonging to the Workout.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.exercises

    def parent_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogReadingAgent.agent_steps(f"\t---------Retrieving Information for Workout Exercise Scheduling---------")
        user_workout_day = state["user_phase_component"]

        return {
            "phase_component_id": user_workout_day["id"],
            "loading_system_id": user_workout_day["loading_system_id"]
        }

    # Print output.
    def get_formatted_list(self, state: AgentState):
        LogReadingAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
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
        LogReadingAgent.formatted_schedule(formatted_schedule["formatted"])

        return {
            self.focus_names["formatted"]: formatted_schedule["formatted"], 
            self.focus_names["list_output"]: formatted_schedule["list"], 
        }


    # Print output.
    def get_user_list(self, state: AgentState):
        LogReadingAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_id = state["user_id"]

        schedule_from_db = self.user_list_query(user_id)
        if not schedule_from_db:
            abort(404, description=f"No {self.focus}s found for the user.")

        user_workout_exercises_dict = [user_workout_exercise.to_dict() | 
                                    {"component_id": user_workout_exercise.phase_components.components.id}
                                    for user_workout_exercise in schedule_from_db]

        formatted_schedule = self.list_printer_class.run_printer(user_workout_exercises_dict)
        LogReadingAgent.formatted_schedule(formatted_schedule["formatted"])

        return {
            self.focus_names["formatted"]: formatted_schedule["formatted"], 
            self.focus_names["list_output"]: formatted_schedule["list"], 
        }

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("read_operation_is_plural", self.chained_conditional_inbetween)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "retrieve_information")
        workflow.add_edge("retrieve_information", "read_operation_is_plural")


        # Whether the plural list is for all of the elements or all elements belonging to the user.
        workflow.add_conditional_edges(
            "read_operation_is_plural",
            determine_read_filter_operation, 
            {
                "current": "get_formatted_list",                        # Read the current schedule.
                "all": "get_user_list"                                  # Read all user elements.
            }
        )

        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)