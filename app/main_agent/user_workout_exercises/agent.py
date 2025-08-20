from config import request_schedule_edits
from logging_config import LogMainSubAgent
from flask import abort
import copy

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app import db
from app.models import User_Workout_Exercises, User_Workout_Days
from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

from app.agents.exercises import exercises_main
from app.utils.common_table_queries import current_workout_day

from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.with_availability import BaseAgentWithAvailability as BaseAgent
from app.main_agent.base_sub_agents.utils import new_input_request
from app.main_agent.user_workout_days import create_microcycle_scheduler_agent
from app.impact_goal_models import PhaseComponentGoal
from app.goal_prompts import phase_component_system_prompt

from .actions import retrieve_availability_for_day, retrieve_parameters
from .edit_goal_model import EditGoal
from .edit_prompts import WorkoutScheduleEditPrompt
from app.schedule_printers import WorkoutScheduleSchedulePrinter
from app.list_printers import workout_schedule_list_printer_main

# ----------------------------------------- User Workout Exercises -----------------------------------------

keys_to_remove = [
    # "id", 
    "workout_day_id", 
    "phase_component_id", 
    "bodypart_id", 
    "exercise_id", 
    "exercise_index", 
    "date", 
    "phase_component_index", 

    "phase_component_name", 
    "bodypart_name", 

    "volume", 
    "performance", 
    "density", 

    "true_exercise_flag", 
    "is_warmup", 
    "working_duration", 
    "intensity", 
    "one_rep_max", 

    "strained_duration", 
    "strained_working_duration", 
    "base_strain", 
    "component_id", 
    "warmup", 
    "i", 
]

# Method to remove keys from the schedule that aren't useful for the LLM.
def remove_unnecessary_keys_from_workout_schedule(schedule_list):
    for exercise in schedule_list:
        # Add unit of measurementforrequired fields.
        exercise["seconds_per_exercise"] = f"{exercise["seconds_per_exercise"]} seconds"
        exercise["reps"] = f"{exercise["reps"]} reps"
        exercise["sets"] = f"{exercise["sets"]} sets"
        exercise["rest"] = f"{exercise["rest"]} seconds"
        exercise["duration"] = f"{exercise["duration"]} seconds"
        exercise["weight"] = f"{exercise["weight"]} lbs"

        # Remove all items not useful for the AI
        for key_to_remove in keys_to_remove:
            exercise.pop(key_to_remove, None)
    return schedule_list

# Method to get the list names and ids.
def get_ids_and_names(list_of_dicts):
    string_output = ", \n".join(
        f"{{{{'id': {e["exercise_index"]}, 'exercise_name': {e["exercise_name"]}}}}}"
        for e in list_of_dicts
    )
    return f"[{string_output}]"

# Method to format a dictionary element to a string.
def dict_to_string(dict_item):
    string_output = ", ".join(
        f"'{key}': '{value}'" 
        for key, value in dict_item.items()
        if key != "id"
    )
    return f"'id': {dict_item["id"]}, {string_output}"

# Method to format the workout summary for the LLM.
def list_of_dicts_to_string(list_of_dicts):
    string_output = ", \n".join(
        f"{{{{{dict_to_string(list_item)}}}}}"
        for list_item in list_of_dicts
    )
    return f"[{string_output}]"

class AgentState(MainAgentState):
    user_phase_component: dict
    phase_component_id: int
    loading_system_id: int

    user_availability: int
    start_date: any
    agent_output: list
    schedule_printed: str

class SubAgent(BaseAgent, WorkoutScheduleSchedulePrinter, WorkoutScheduleEditPrompt):
    focus = "workout_schedule"
    parent = "phase_component"
    sub_agent_title = "User Workout"
    parent_title = "Phase Component"
    parent_system_prompt = phase_component_system_prompt
    parent_goal = PhaseComponentGoal
    parent_scheduler_agent = create_microcycle_scheduler_agent()

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

    # Format the structured schedule.
    def format_proposed_list(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Format Proposed Workout Schedule---------")
        schedule_list = state["agent_output"]

        for schedule_item in schedule_list:
            schedule_item["id"] = schedule_item["exercise_index"]
            schedule_item["phase_component_subcomponent"] = schedule_item["phase_component_name"]
            schedule_item["bodypart"] = schedule_item["bodypart_name"]
            schedule_item["is_warmup"] = schedule_item["warmup"]

        formatted_schedule = workout_schedule_list_printer_main(schedule_list)
        LogMainSubAgent.formatted_schedule(formatted_schedule)

        return {"schedule_printed": formatted_schedule}

    # Create prompt to request schedule edits.
    def edit_prompt_creator(self, schedule_list_original):
        allowed_list = get_ids_and_names(schedule_list_original)
        schedule_list = remove_unnecessary_keys_from_workout_schedule(schedule_list_original)
        schedule_summary = list_of_dicts_to_string(schedule_list)
        edit_prompt = self.edit_system_prompt_constructor(schedule_summary, allowed_list)
        return edit_prompt

    # Items extracted from the edit request.
    def goal_edits_parser(self, goal_edits=None):
        # Return an empty dictionary of edits if no edits were made.
        if not goal_edits:
            return {}
    
        goal_edits_dict={}
        
        # Convert goal edits to a dictionary format
        for goal_edit in goal_edits:
            goal_edit_information = {
                "exercise_index": goal_edit.id, 
                "remove": goal_edit.remove, 
                "reps": goal_edit.reps, 
                "sets": goal_edit.sets, 
                "rest": goal_edit.rest, 
                "weight": goal_edit.weight, 
            }

            goal_edits_dict[goal_edit.id] = goal_edit_information

        return goal_edits_dict

    # Retrieve entry for the edit.
    def compare_edits(self, original_schedule, altered_schedule):
        edits_to_be_applyed = {}
        for original_schedule_item in original_schedule:
            original_schedule_item_id = original_schedule_item["exercise_index"]

            # Skip the entry if the schedule item isn't present.
            if original_schedule_item_id not in altered_schedule.keys():
                continue

            altered_schedule_item = altered_schedule[original_schedule_item_id]

            common_keys = set(original_schedule_item.keys()) & set(altered_schedule_item.keys())

            # Include the item if it has been indicated to be removed.
            if altered_schedule_item["remove"]:
                edits_to_be_applyed[original_schedule_item_id] = altered_schedule_item

            # Only include the item if any value has been changed from the original.
            elif any(original_schedule_item[key] != altered_schedule_item[key] for key in common_keys):
                edits_to_be_applyed[original_schedule_item_id] = altered_schedule_item
        return edits_to_be_applyed

    # Items extracted from the edit request.
    def goal_edit_request_parser(self, goal_class, edits_to_be_applyed):
        return {
            "is_edited": True if edits_to_be_applyed else False,
            "edits": edits_to_be_applyed,
            # "should_regenerate": goal_class.regenerate,
            "other_requests": goal_class.other_requests
        }

    # Request permission from user to execute the parent initialization.
    def ask_for_edits(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Ask user if edits should be made to the schedule---------")
        if not request_schedule_edits:
            LogMainSubAgent.agent_steps(f"\t---------Agent settings do not request edits.---------")
            return {
                "is_edited": False,
                "edits": {},
                # "should_regenerate": False,
                "other_requests": None
            }
        # Get a copy of the current schedule and remove the items not useful for the AI.
        formatted_schedule_list = state["schedule_printed"]

        result = interrupt({
            "task": f"Are there any edits you would like to make to the schedule?\n\n{formatted_schedule_list}"
        })
        user_input = result["user_input"]
        LogMainSubAgent.verbose(f"Extract the {self.sub_agent_title} Goal the following message: {user_input}")

        # Retrieve the schedule and format it for the prompt.
        schedule_list = state["agent_output"]
        edit_prompt = self.edit_prompt_creator(copy.deepcopy(schedule_list))

        # Retrieve the new input for the parent item.
        goal_class = new_input_request(user_input, edit_prompt, EditGoal)

        new_schedule = goal_class.schedule
        if new_schedule: 
            # Convert to dictionary form.
            goal_edits_dict = self.goal_edits_parser(new_schedule)

            # Refine and remove entries that weren't edited.
            edits_to_be_applyed = self.compare_edits(state["agent_output"], goal_edits_dict)
        else: 
            edits_to_be_applyed = {}

        return self.goal_edit_request_parser(goal_class, edits_to_be_applyed)

    # Confirm that the desired section should be edited.
    def confirm_edits(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Confirm that the {self.sub_agent_title} is Edited---------")
        if state["is_edited"]:
        # if state["edits"]:
            LogMainSubAgent.agent_steps(f"\t---------Is Edited---------")
            return "is_edited"
        return "not_edited"

    # Perform the edits.
    def perform_edits(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Performing the Requested Edits for {self.sub_agent_title}---------")

        # Retrieve the schedule and format it for the prompt.
        schedule_list = state["agent_output"]
        schedule_edits = state["edits"]

        # Apply the schedule edits to the workout exercises.
        for schedule_item in schedule_list:
            # Skip the entry if the schedule item isn't present.
            if schedule_item["exercise_index"] not in schedule_edits.keys():
                continue

            schedule_edit = schedule_edits[schedule_item["exercise_index"]]

            schedule_item["reps"] = schedule_edit["reps"]
            schedule_item["sets"] = schedule_edit["sets"]
            schedule_item["rest"] = schedule_edit["rest"]

            # In case a weight is accidentally applied to a non-weighted exercises
            if schedule_item["weight"]:
                schedule_item["weight"] = schedule_edit["weight"]

                # Calculate new intensity.
                schedule_item["intensity"] = schedule_item["weight"] / schedule_item["one_rep_max"]
        
        return {"agent_output": schedule_list}

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

        formatted_schedule = self.run_schedule_printer(workout_date, loading_system_id, user_workout_exercises_dict)
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

        formatted_schedule = workout_schedule_list_printer_main(user_workout_exercises_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
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
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("perform_scheduler", self.perform_scheduler)
        workflow.add_node("format_proposed_list", self.format_proposed_list)
        workflow.add_node("ask_for_edits", self.ask_for_edits)
        workflow.add_node("perform_edits", self.perform_edits)
        workflow.add_node("agent_output_to_sqlalchemy_model", self.agent_output_to_sqlalchemy_model)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_conditional_edges(
            START,
            self.confirm_impact,
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "retrieve_parent"                             # Retrieve the parent element if an impact is indicated.
            }
        )

        # Whether a parent element exists.
        workflow.add_conditional_edges(
            "retrieve_parent",
            self.confirm_parent,
            {
                "no_parent": "ask_for_permission",                      # No parent element exists.
                "parent": "parent_retrieved"                            # Retreive the availability for the alteration.
            }
        )
        workflow.add_edge("parent_retrieved", "retrieve_availability")


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

        # Whether an availability for the user exists.
        workflow.add_conditional_edges(
            "retrieve_availability",
            self.confirm_availability,
            {
                "no_availability": "ask_for_availability_permission",   # No parent element exists.
                "availability": "retrieve_information"                  # Retrieve the information for the alteration.
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
        workflow.add_edge("availability", "retrieve_parent")

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

        workflow.add_edge("delete_old_children", "perform_scheduler")
        workflow.add_edge("perform_scheduler", "format_proposed_list")
        workflow.add_edge("format_proposed_list", "ask_for_edits")

        workflow.add_conditional_edges(
            "ask_for_edits",
            self.confirm_edits,
            {
                "is_edited": "perform_edits",
                "not_edited": "agent_output_to_sqlalchemy_model"
            }
        )
        workflow.add_edge("perform_edits", "format_proposed_list")

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