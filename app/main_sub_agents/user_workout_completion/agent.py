from logging_config import LogMainSubAgent

from langgraph.graph import StateGraph, START, END

# Database imports.
from app import db
from app.models import User_Exercises
from app.common_table_queries.phase_components import currently_active_item as current_workout_day

# Agent construction imports.
from app.main_sub_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.main_sub_agents.base_sub_agents.base import confirm_impact
from app.agent_states.workout_completion import AgentState
from app.schedule_printers.workout_completion import WorkoutCompletionSchedulePrinter

# Sub agent imports.
from app.edit_agents.workout_completion import create_main_agent_graph as create_workout_completion_edit_agent

# ----------------------------------------- User Workout Completion -----------------------------------------

# Confirm that there is a workout to complete.
def confirm_children(state: AgentState):
    LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active Workout---------")
    if not state.get("agent_output", None):
        return "no_schedule"
    return "present_schedule"


# Confirm that a currently active parent exists to attach the a schedule to.
def confirm_parent(state: AgentState):
    LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active workout_day---------")
    if not state.get("user_workout_day", None):
        return "no_parent"
    return "parent"

class SubAgent(BaseAgent):
    focus = "workout_completion"
    sub_agent_title = "Workout Completion"
    focus_edit_agent = create_workout_completion_edit_agent()
    schedule_printer_class = WorkoutCompletionSchedulePrinter()

    # def focus_retriever_agent(self, user_id):
    #     return current_workout_day(user_id)

    def parent_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    # Retrieve parent item that will be used for the current schedule.
    def retrieve_parent(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Current Workout Day---------")
        user_id = state["user_id"]
        parent_db_entry = self.parent_retriever_agent(user_id)

        # Return parent.
        return {"user_workout_day": parent_db_entry.to_dict() if parent_db_entry else None}

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for {self.sub_agent_title}---------")
        user_workout_day = state["user_workout_day"]

        return {
            "agent_output": user_workout_day["exercises"], 
            "workout_day_id": user_workout_day["id"]
        }

    # Initializes the microcycle schedule for the current mesocycle.
    def perform_workout_completion(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Perform {self.sub_agent_title}---------")
        user_id = state["user_id"]
        workout_exercises = state["agent_output"]

        user_exercises = []
        old_user_exercises = []
        for exercise in workout_exercises:
            # Retrieve corresponding user exercise entry.
            user_exercise = db.session.get(
                User_Exercises, {
                    "user_id": user_id, 
                    "exercise_id": exercise["exercise_id"]})

            # Append old exercise performance for formatted schedule later.
            old_user_exercises.append(user_exercise.to_dict())

            # Only replace if the new one rep max is larger.
            user_exercise.one_rep_max = max(user_exercise.one_rep_max_decayed, exercise["one_rep_max"])
            user_exercise.one_rep_load = exercise["one_rep_max"]
            user_exercise.volume = exercise["volume"]
            user_exercise.density = exercise["density"]
            user_exercise.intensity = exercise["intensity"]
            user_exercise.duration = exercise["duration"]
            user_exercise.working_duration = exercise["working_duration"]
            user_exercise.last_performed = exercise["date"]

            # Only replace if the new performance is larger.
            user_exercise.performance = max(user_exercise.performance_decayed, exercise["performance"])

            db.session.commit()

            # Append new exercise performance for formatted schedule later.
            user_exercises.append(user_exercise.to_dict())

        return {
            "user_exercises": user_exercises, 
            "old_user_exercises": old_user_exercises
        }

    # Print output.
    def get_formatted_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_exercises = state["user_exercises"]
        old_user_exercises = state["old_user_exercises"]

        formatted_schedule = self.schedule_printer_class.run_printer(old_user_exercises, user_exercises)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("editor_agent", self.focus_edit_agent)
        workflow.add_node("perform_workout_completion", self.perform_workout_completion)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
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

        workflow.add_conditional_edges(
            "retrieve_parent",
            confirm_parent, 
            {
                "no_parent": "end_node",                                # No parent element exists.
                "parent": "retrieve_information"                        # Retrieve the information for the alteration.
            }
        )

        workflow.add_conditional_edges(
            "retrieve_information",
            confirm_children,
            {
                "no_schedule": "end_node",                              # End the sub agent if no schedule is found.
                "present_schedule": "editor_agent"                      # Fromat the proposed list for the user if a schedule exists.
            }
        )

        workflow.add_edge("editor_agent", "perform_workout_completion")
        workflow.add_edge("perform_workout_completion", "get_formatted_list")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)