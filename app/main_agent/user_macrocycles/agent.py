from logging_config import LogMainSubAgent
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from app import db
from app.agents.goals import create_goal_classification_graph
from app.db_session import session_scope
from app.models import Goal_Library, User_Macrocycles, User_Mesocycles
from app.utils.common_table_queries import current_macrocycle

from app.main_agent.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.impact_goal_models import MacrocycleGoal
from app.goal_prompts import macrocycle_system_prompt
from app.edit_agents import create_macrocycle_edit_agent

from .actions import retrieve_goal_types
from app.schedule_printers import MacrocycleSchedulePrinter

# ----------------------------------------- User Macrocycles -----------------------------------------

class AgentState(TypedDict):
    user_id: int
    focus_name: str

    user_input: str
    attempts: int
    other_requests: str

    macrocycle_impacted: bool
    macrocycle_is_altered: bool
    macrocycle_read_plural: bool
    macrocycle_read_current: bool
    macrocycle_message: str
    macrocycle_formatted: str
    macrocycle_perform_with_parent_id: int
    macrocycle_alter_old: bool

    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int


class SubAgent(BaseAgent):
    focus = "macrocycle"
    sub_agent_title = "Macrocycle"
    focus_system_prompt = macrocycle_system_prompt
    focus_goal = MacrocycleGoal
    focus_edit_agent = create_macrocycle_edit_agent()
    schedule_printer_class = MacrocycleSchedulePrinter()

    def user_list_query(self, user_id):
        return User_Macrocycles.query.filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    def focus_list_retriever_agent(self, user_id):
        return [current_macrocycle(user_id)]

    # Items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        return {
            focus_names["impact"]: goal_class.is_requested,
            focus_names["is_altered"]: True,
            focus_names["read_plural"]: False,
            focus_names["read_current"]: False, 
            focus_names["message"]: goal_class.detail, 
            "other_requests": goal_class.other_requests, 
            "macrocycle_alter_old": goal_class.alter_old or False
        }

    # Perform the goal change to the desired ID.
    def perform_goal_change_by_id(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Perform {self.sub_agent_title} ID Assignment---------")
        goal_id = state[self.focus_names["perform_with_parent_id"]]
        goal_entry_from_db = db.session.get(Goal_Library, goal_id)
        goal = goal_entry_from_db.to_dict()

        user_id = state["user_id"]
        user_macrocycle = current_macrocycle(user_id)
        
        return {
            "user_macrocycle": user_macrocycle.to_dict() if user_macrocycle else None,
            "goal_id": goal_id, 
            self.focus_names["message"]: goal["name"]
        }

    # Classify the new goal in one of the possible goal types.
    def perform_input_parser(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Perform {self.sub_agent_title} Classifier---------")
        new_goal = state["macrocycle_message"]

        # There are only so many goal types a macrocycle can be classified as, with all of them being stored.
        goal_types = retrieve_goal_types()
        goal_app = create_goal_classification_graph()

        user_id = state["user_id"]
        user_macrocycle = current_macrocycle(user_id)

        # Invoke with new macrocycle and possible goal types.
        goal = goal_app.invoke({
            "new_goal": new_goal, 
            "goal_types": goal_types, 
            "attempts": 0})
        
        return {
            "user_macrocycle": user_macrocycle.to_dict() if user_macrocycle else None,
            "goal_id": goal["goal_id"]
        }

    # Determine whether the current macrocycle should be edited or if a new one should be created.
    def which_operation(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Determine whether goal should be new---------")
        if state["macrocycle_alter_old"] and state["user_macrocycle"]:
            return "alter_old_macrocycle"
        return "create_new_macrocycle"

    # Creates the new macrocycle of the determined type.
    def create_new_macrocycle(self, state: AgentState):
        user_id = state["user_id"]
        goal_id = state["goal_id"]
        new_goal = state["macrocycle_message"]
        payload = {}
        with session_scope() as s:
            user_macrocycle = User_Macrocycles(user_id=user_id, goal_id=goal_id, goal=new_goal)
            s.add(user_macrocycle)

            # get PKs without committing the transaction
            s.flush()

            # load defaults/server-side values
            s.refresh(user_macrocycle)
            payload = user_macrocycle.to_dict()

        return {"user_macrocycle": payload}

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for Macrocycle Changing---------")
        user_macrocycle = state["user_macrocycle"]
        return {
            "macrocycle_id": user_macrocycle["id"], 
            "start_date": user_macrocycle["start_date"], 
            "end_date": user_macrocycle["end_date"], 
        }

    # Delete the old children belonging to the current item.
    def delete_old_children(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Delete old items of current Macrocycle---------")
        macrocycle_id = state["macrocycle_id"]
        with session_scope() as s:
            s.query(User_Mesocycles).filter_by(macrocycle_id=macrocycle_id).delete()
        LogMainSubAgent.verbose("Successfully deleted")
        return {}

    # Alters the current macrocycle to be the determined type.
    def alter_old_macrocycle(self, state: AgentState):
        goal_id = state["goal_id"]
        new_goal = state["macrocycle_message"]
        macrocycle_id = state["macrocycle_id"]
        payload = {}
        with session_scope() as s:
            user_macrocycle = s.get(User_Macrocycles, macrocycle_id)
            user_macrocycle.goal = new_goal
            user_macrocycle.goal_id = goal_id

            # get PKs without committing the transaction
            s.flush()

            # load defaults/server-side values
            s.refresh(user_macrocycle)
            payload = user_macrocycle.to_dict()

        return {"user_macrocycle": payload}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_alter", self.chained_conditional_inbetween)
        workflow.add_node("perform_goal_change_by_id", self.perform_goal_change_by_id)
        workflow.add_node("alter_operation_uses_agent", self.chained_conditional_inbetween)
        workflow.add_node("ask_for_new_input", self.ask_for_new_input)
        workflow.add_node("perform_input_parser", self.perform_input_parser)
        workflow.add_node("create_new_macrocycle", self.create_new_macrocycle)
        workflow.add_node("editor_agent_for_creation", self.focus_edit_agent)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("editor_agent_for_alteration", self.focus_edit_agent)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("alter_old_macrocycle", self.alter_old_macrocycle)
        workflow.add_node("read_user_current_element", self.read_user_current_element)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("no_new_input_requested", self.no_new_input_requested)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            self.confirm_impact,
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "impact_confirmed"                            # In between step for if an impact is indicated.
            }
        )

        # Whether the goal is to read or alter user elements.
        workflow.add_conditional_edges(
            "impact_confirmed",
            self.determine_operation,
            {
                "read": "operation_is_read",                            # In between step for if the operation is read.
                "alter": "operation_is_alter"                           # In between step for if the operation is alter.
            }
        )

        # Whether the read operations is for a single element or plural elements.
        workflow.add_conditional_edges(
            "operation_is_read",
            self.determine_read_operation,
            {
                "plural": "get_user_list",                              # Read all user elements.
                "singular": "read_user_current_element"                 # Read the current element.
            }
        )

        # Whether goal should be changed to the included id.
        workflow.add_conditional_edges(
            "operation_is_alter",
            self.confirm_if_performing_by_id,
            {
                "no_direct_goal_id": "alter_operation_uses_agent",           # Perform LLM parser if no goal id is included.
                "present_direct_goal_id": "perform_goal_change_by_id"             # Perform direct id assignment if a goal id is included.
            }
        )

        # Whether the intention is to alter the current macrocycle or to create a new one.
        workflow.add_conditional_edges(
            "perform_goal_change_by_id",
            self.which_operation,
            {
                "alter_old_macrocycle": "retrieve_information",             # Alter the current macrocycle.
                "create_new_macrocycle": "editor_agent_for_creation"        # Create a new macrocycle.
            }
        )

        # Whether there is a new goal to perform the change with.
        workflow.add_conditional_edges(
            "alter_operation_uses_agent",
            self.confirm_new_input,
            {
                "no_new_input": "ask_for_new_input",                    # Request a new macrocycle goal if one isn't present.
                "present_new_input": "perform_input_parser"             # Parse the goal for what category it falls into if one is present.
            }
        )

        # Whether there is a new goal to perform the change with.
        workflow.add_conditional_edges(
            "ask_for_new_input",
            self.confirm_new_input,
            {
                "no_new_input": "no_new_input_requested",               # Indicate that no new goal was given.
                "present_new_input": "perform_input_parser"             # Parse the goal for what category it falls into if one is present.
            }
        )

        # Whether the intention is to alter the current macrocycle or to create a new one.
        workflow.add_conditional_edges(
            "perform_input_parser",
            self.which_operation,
            {
                "alter_old_macrocycle": "retrieve_information",             # Alter the current macrocycle.
                "create_new_macrocycle": "editor_agent_for_creation"        # Create a new macrocycle.
            }
        )

        workflow.add_edge("editor_agent_for_creation", "create_new_macrocycle")

        workflow.add_edge("retrieve_information", "editor_agent_for_alteration")
        workflow.add_edge("editor_agent_for_alteration", "delete_old_children")
        workflow.add_edge("delete_old_children", "alter_old_macrocycle")
        workflow.add_edge("alter_old_macrocycle", "read_user_current_element")
        workflow.add_edge("create_new_macrocycle", "read_user_current_element")
        workflow.add_edge("no_new_input_requested", "end_node")
        workflow.add_edge("read_user_current_element", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)