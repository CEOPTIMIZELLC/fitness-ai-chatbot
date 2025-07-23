from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from flask import current_app, abort
from typing_extensions import TypeVar

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app import db
from app.main_agent.main_agent_state import MainAgentState

from .utils import sub_agent_focused_items

# ----------------------------------------- Base Sub Agent For Schedule Items With Parents -----------------------------------------

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=MainAgentState)

class BaseAgentWithParents():
    focus = ""
    parent = ""
    sub_agent_title = ""
    parent_title = ""
    parent_system_prompt = None
    parent_goal = None
    parent_scheduler_agent = None
    schedule_printer_class = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)
        self.parent_names = sub_agent_focused_items(self.parent)

    def retrieve_children_entries_from_parent(self, parent_db_entry):
        pass

    def user_list_query(self, user_id):
        pass

    def focus_retriever_agent(self, user_id):
        pass

    def parent_retriever_agent(self, user_id):
        pass

    # In between node for chained conditional edges.
    def chained_conditional_inbetween(self, state: TState):
        return {}

    # Confirm that the desired section should be impacted.
    def confirm_impact(self, state: TState):
        if verbose_agent_introductions:
            print(f"\n=========Beginning User {self.sub_agent_title} Sub Agent=========")
        if verbose_subagent_steps:
            print(f"\t---------Confirm that the {self.sub_agent_title} is Impacted---------")
        if not state[self.focus_names["impact"]]:
            if verbose_subagent_steps:
                print(f"\t---------No Impact---------")
            return "no_impact"
        return "impact"

    # Retrieve parent item that will be used for the current schedule.
    def retrieve_parent(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Current {self.parent_title}---------")
        user_id = state["user_id"]
        parent_db_entry = self.parent_retriever_agent(user_id)

        # Return parent.
        return {self.parent_names["entry"]: parent_db_entry.to_dict() if parent_db_entry else None}

    # Confirm that a currently active parent exists to attach the a schedule to.
    def confirm_parent(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Confirm there is an active {self.parent_title}---------")
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
            if verbose_subagent_steps:
                print(f"\t---------Change parent id of {self.parent_title}---------")
            user_id = state["user_id"]
            new_parent_id = state[perform_with_parent_id_key]
            parent_db_entry = self.parent_changer(user_id, new_parent_id)

            db.session.commit()

            # Return new parent.
            return {self.parent_names["entry"]: parent_db_entry.to_dict() if parent_db_entry else None}

        return {}

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, parent_names, goal_class):
        return {
            parent_names["impact"]: goal_class.is_requested,
            parent_names["is_altered"]: True,
            parent_names["read_plural"]: False,
            parent_names["read_current"]: False,
            parent_names["message"]: goal_class.detail
        }

    # Request permission from user to execute the parent initialization.
    def ask_for_permission(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Ask user if a new {self.parent_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.parent_title} exists for {self.sub_agent_title}. Would you like for me to generate a {self.parent_title} for you?"
        })
        user_input = result["user_input"]

        print(f"Extract the {self.parent_title} Goal the following message: {user_input}")
        human = f"Extract the goals from the following message: {user_input}"
        check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.parent_system_prompt),
                ("human", human),
            ]
        )
        llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
        structured_llm = llm.with_structured_output(self.parent_goal)
        goal_classifier = check_prompt | structured_llm
        goal_class = goal_classifier.invoke({})

        return self.goal_classifier_parser(self.parent_names, goal_class)

    # Router for if permission was granted.
    def confirm_permission(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Confirm the agent can create a new {self.parent_title}---------")
        if not state[self.parent_names["impact"]]:
            return "permission_denied"
        return "permission_granted"

    # State if the Parent isn't allowed to be requested.
    def permission_denied(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Abort {self.sub_agent_title} Scheduling---------")
        abort(404, description=f"No active {self.parent_title} found.")
        return {}

    # Determine the operation to be performed.
    def determine_operation(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Determine if the objective is to read or write {self.sub_agent_title}---------")
        if state[self.focus_names["is_altered"]]:
            return "alter"
        return "read"

    # Determine whether the outcome is to read the entire schedule or simply the current item.
    def determine_read_operation(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Determine if the objective is to read a list of {self.sub_agent_title} or simply a singular item---------")
        if state[self.focus_names["read_plural"]]:
            return "plural"
        return "singular"

    # Determine whether the outcome is to read an item from the current set or all items from the user.
    def determine_read_filter_operation(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Determine if the objective is to read all {self.sub_agent_title} items for the user or only those currently active---------")
        if state[self.focus_names["read_current"]]:
            return "current"
        return "all"

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: TState):
        pass

    def delete_children_query(self, parent_id):
        pass

    # Delete the old items belonging to the parent.
    def delete_old_children(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Delete old {self.sub_agent_title}s---------")
        parent_id = state[self.parent_names["id"]]
        self.delete_children_query(parent_id)
        if verbose:
            print("Successfully deleted")
        return {}

    # Initializes the scheduler for the current parent.
    def perform_scheduler(self, state: TState):
        pass

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: TState):
        pass

    # Retrieve user's current schedule item.
    def read_user_current_element(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Current {self.sub_agent_title} for User---------")
        user_id = state["user_id"]

        entry_from_db = self.focus_retriever_agent(user_id)
        if not entry_from_db:
            abort(404, description=f"No active {self.sub_agent_title} found.")

        schedule_dict = [entry_from_db.to_dict()]
        formatted_schedule = self.run_schedule_printer(schedule_dict)
        if verbose_formatted_schedule:
            print(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Print output.
    def get_formatted_list(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_id = state["user_id"]
        parent_db_entry = self.parent_retriever_agent(user_id)

        schedule_from_db = self.retrieve_children_entries_from_parent(parent_db_entry)
        if not schedule_from_db:
            abort(404, description=f"No {self.focus}s found for the {self.parent}.")

        schedule_dict = [schedule_entry.to_dict() for schedule_entry in schedule_from_db]

        formatted_schedule = self.run_schedule_printer(schedule_dict)
        if verbose_formatted_schedule:
            print(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Print output.
    def get_user_list(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_id = state["user_id"]

        schedule_from_db = self.user_list_query(user_id)
        if not schedule_from_db:
            abort(404, description=f"No {self.focus}s found for the user.")

        schedule_dict = [schedule_entry.to_dict() for schedule_entry in schedule_from_db]

        formatted_schedule = self.run_schedule_printer(schedule_dict)
        if verbose_formatted_schedule:
            print(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Node to declare that the sub agent has ended.
    def end_node(self, state: TState):
        if verbose_agent_introductions:
            print(f"=========Ending User {self.sub_agent_title} SubAgent=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class: type[TState]):
        workflow = StateGraph(state_class)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("ask_for_permission", self.ask_for_permission)
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
                "impact": "retrieve_parent"                             # Retrieve the parent element if an impact is indicated.
            }
        )

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
        workflow.add_conditional_edges(
            "ask_for_permission",
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
        workflow.add_edge("read_user_current_element", "end_node")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()