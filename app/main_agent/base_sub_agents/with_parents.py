from logging_config import LogMainSubAgent
from flask import abort
from typing_extensions import TypeVar

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app import db
from app.main_agent.main_agent_state import MainAgentState

from .base import BaseAgent
from .utils import sub_agent_focused_items, new_input_request, user_input_information_extraction, agent_state_update

# ----------------------------------------- Base Sub Agent For Schedule Items With Parents -----------------------------------------

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class BaseAgentWithParents(BaseAgent):
    parent = ""
    parent_title = ""
    parent_system_prompt = None
    parent_goal = None
    parent_scheduler_agent = None
    focus_edit_agent = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)
        self.parent_names = sub_agent_focused_items(self.parent)

    def parent_retriever_agent(self, user_id):
        pass

    def retrieve_children_entries_from_parent(self, parent_db_entry):
        pass

    # Node to declare that the sub agent has begun.
    def start_node(self, state):
        LogMainSubAgent.agent_introductions(f"\n=========Beginning User {self.sub_agent_title} Sub Agent=========")
        return {
            "focus_name": self.focus, 
            "parent_name": self.parent, 
        }

    # Focus List Retriever uses the parent retriever and then retrieves the children from it.
    def focus_list_retriever_agent(self, user_id):
        parent_db_entry = self.parent_retriever_agent(user_id)

        schedule_from_db = self.retrieve_children_entries_from_parent(parent_db_entry)
        if not schedule_from_db:
            abort(404, description=f"No {self.focus}s found for the {self.parent}.")
        return schedule_from_db

    # Retrieve parent item that will be used for the current schedule.
    def retrieve_parent(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Current {self.parent_title}---------")
        user_id = state["user_id"]
        parent_db_entry = self.parent_retriever_agent(user_id)

        # Return parent.
        return {self.parent_names["entry"]: parent_db_entry.to_dict() if parent_db_entry else None}

    # Confirm that a currently active parent exists to attach the a schedule to.
    def confirm_parent(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Confirm there is an active {self.parent_title}---------")
        if not state[self.parent_names["entry"]]:
            return "no_parent"
        return "parent"

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        pass

    # In between node for when the parent is retrieved.
    def parent_retrieved(self, state: TState):
        # Change the parent id if performing it with a different id has been specified.
        perform_with_parent_id_key = self.focus_names["perform_with_parent_id"]
        if perform_with_parent_id_key in state and state[perform_with_parent_id_key]:
            LogMainSubAgent.agent_steps(f"\t---------Change parent id of {self.parent_title}---------")
            user_id = state["user_id"]
            new_parent_id = state[perform_with_parent_id_key]
            parent_db_entry = self.parent_changer(user_id, new_parent_id)

            db.session.commit()

            # Return new parent.
            return {self.parent_names["entry"]: parent_db_entry.to_dict() if parent_db_entry else None}

        return {}

    # Request permission from user to execute the parent initialization.
    def ask_for_permission(self, state: TState):
        # If the permission has already been given, move on ahead.
        if state[self.parent_names["impact"]]:
            LogMainSubAgent.agent_steps(f"\t---------Permission already granted---------")
            return {}
        LogMainSubAgent.agent_steps(f"\t---------Ask user if a new {self.parent_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.parent_title} exists for {self.sub_agent_title}. Would you like for me to generate a {self.parent_title} for you?"
        })
        user_input = result["user_input"]
        LogMainSubAgent.verbose(f"Extract the {self.parent_title} Goal the following message: {user_input}")

        # Retrieve the new input for the parent item.
        goal_class = new_input_request(user_input, self.parent_system_prompt, self.parent_goal)

        # Parse the structured output values to a dictionary.
        return self.goal_classifier_parser(self.parent_names, goal_class)

    def other_requests_information_extractor(self, state, ignore_section, other_requests="other_requests"):
        # Retrieve the other requests.
        user_input = state.get(other_requests)
        if not user_input:
            LogMainSubAgent.agent_steps(f"\n---------No Other Requests---------")
            return {}

        LogMainSubAgent.verbose(f"Extract the goals from the following message: {user_input}")

        updated_state = user_input_information_extraction(user_input)

        result = agent_state_update(state, updated_state, ignore_section)

        LogMainSubAgent.input_info(f"Goals extracted.")
        if result.get("workout_completion_impacted"):
            LogMainSubAgent.input_info(f"workout_completion: {result["workout_completion_message"]}")
        if result.get("availability_impacted"):
            LogMainSubAgent.input_info(f"availability: {result["availability_message"]}")
        if result.get("macrocycle_impacted"):
            LogMainSubAgent.input_info(f"macrocycle: {result["macrocycle_message"]}")
        if result.get("mesocycle_impacted"):
            LogMainSubAgent.input_info(f"mesocycle: {result["mesocycle_message"]}")
        if result.get("microcycle_impacted"):
            LogMainSubAgent.input_info(f"microcycle: {result["microcycle_message"]}")
        if result.get("phase_component_impacted"):
            LogMainSubAgent.input_info(f"phase_component: {result["phase_component_message"]}")
        if result.get("workout_schedule_impacted"):
            LogMainSubAgent.input_info(f"workout_schedule: {result["workout_schedule_message"]}")
        LogMainSubAgent.input_info("")

        # Reset other requests to be empty.
        state[other_requests] = None
        return result

    # Find other requests from the previous parent message retrieval.
    def parent_requests_extraction(self, state: TState):
        LogMainSubAgent.agent_steps(f"\n---------Extract Other Requests---------")
        return self.other_requests_information_extractor(state, self.parent)

    # Router for if permission was granted.
    def confirm_permission(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Confirm the agent can create a new {self.parent_title}---------")
        if not state[self.parent_names["impact"]]:
            return "permission_denied"
        return "permission_granted"

    # State if the Parent isn't allowed to be requested.
    def permission_denied(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Abort {self.sub_agent_title} Scheduling---------")
        abort(404, description=f"No active {self.parent_title} found.")
        return {}

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: TState):
        pass

    def delete_children_query(self, parent_id):
        pass

    # Delete the old items belonging to the parent.
    def delete_old_children(self, state: TState):
        LogMainSubAgent.agent_steps(f"\t---------Delete old {self.sub_agent_title}s---------")
        parent_id = state[self.parent_names["id"]]
        self.delete_children_query(parent_id)
        LogMainSubAgent.verbose("Successfully deleted")
        return {}

    # Initializes the scheduler for the current parent.
    def perform_scheduler(self, state: TState):
        pass

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: TState):
        pass


    # Create main agent.
    def create_main_agent_graph(self, state_class: type[TState]):
        pass