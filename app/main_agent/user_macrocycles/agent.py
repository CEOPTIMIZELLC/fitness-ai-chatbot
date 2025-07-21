from config import verbose, verbose_subagent_steps
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from app import db
from app.agents.goals import create_goal_classification_graph
from app.models import User_Macrocycles, User_Mesocycles
from app.utils.common_table_queries import current_macrocycle

from app.main_agent.base_sub_agents.without_parents import BaseAgent
from app.main_agent.impact_goal_models import MacrocycleGoal
from app.main_agent.prompts import macrocycle_system_prompt

from .actions import retrieve_goal_types
from .schedule_printer import SchedulePrinter

# ----------------------------------------- User Macrocycles -----------------------------------------

class AgentState(TypedDict):
    user_id: int

    user_input: str
    attempts: int

    macrocycle_impacted: bool
    macrocycle_is_altered: bool
    macrocycle_message: str
    macrocycle_formatted: str
    macrocycle_alter_old: bool

    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int


class SubAgent(BaseAgent, SchedulePrinter):
    focus = "macrocycle"
    sub_agent_title = "Macrocycle"
    focus_system_prompt = macrocycle_system_prompt
    focus_goal = MacrocycleGoal

    def user_list_query(user_id):
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
            focus_names["message"]: goal_class.detail, 
            "macrocycle_alter_old": goal_class.alter_old
        }

    # Classify the new goal in one of the possible goal types.
    def perform_input_parser(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Perform {self.sub_agent_title} Classifier---------")
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
        if verbose_subagent_steps:
            print(f"\t---------Determine whether goal should be new---------")
        if state["macrocycle_alter_old"] and state["user_macrocycle"]:
            return "alter_macrocycle"
        return "create_new_macrocycle"

    # Creates the new macrocycle of the determined type.
    def create_new_macrocycle(self, state: AgentState):
        user_id = state["user_id"]
        goal_id = state["goal_id"]
        new_goal = state["macrocycle_message"]
        new_macrocycle = User_Macrocycles(user_id=user_id, goal_id=goal_id, goal=new_goal)
        db.session.add(new_macrocycle)
        db.session.commit()
        return {"user_macrocycle": new_macrocycle.to_dict()}

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Information for Macrocycle Changing---------")
        user_macrocycle = state["user_macrocycle"]
        macrocycle_id = user_macrocycle["id"]
        return {"macrocycle_id": macrocycle_id}

    # Delete the old children belonging to the current item.
    def delete_old_children(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Delete old items of current Macrocycle---------")
        macrocycle_id = state["macrocycle_id"]
        db.session.query(User_Mesocycles).filter_by(macrocycle_id=macrocycle_id).delete()
        if verbose:
            print("Successfully deleted")
        return {}

    # Alters the current macrocycle to be the determined type.
    def alter_macrocycle(self, state: AgentState):
        goal_id = state["goal_id"]
        new_goal = state["macrocycle_message"]
        macrocycle_id = state["macrocycle_id"]
        user_macrocycle = db.session.get(User_Macrocycles, macrocycle_id)
        user_macrocycle.goal = new_goal
        user_macrocycle.goal_id = goal_id
        db.session.commit()
        return {"user_macrocycle": user_macrocycle.to_dict()}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)

        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("operation_retrieved", self.chained_conditional_inbetween)
        workflow.add_node("ask_for_new_input", self.ask_for_new_input)
        workflow.add_node("perform_input_parser", self.perform_input_parser)
        workflow.add_node("create_new_macrocycle", self.create_new_macrocycle)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("alter_macrocycle", self.alter_macrocycle)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("no_new_input_requested", self.no_new_input_requested)
        workflow.add_node("end_node", self.end_node)

        workflow.add_conditional_edges(
            START,
            self.confirm_impact,
            {
                "no_impact": "end_node",
                "impact": "impact_confirmed"
            }
        )

        workflow.add_conditional_edges(
            "impact_confirmed",
            self.determine_operation,
            {
                "read": "get_formatted_list",
                "alter": "operation_retrieved"
            }
        )

        workflow.add_conditional_edges(
            "operation_retrieved",
            self.confirm_new_input,
            {
                "no_new_input": "ask_for_new_input",
                "present_new_input": "perform_input_parser"
            }
        )

        workflow.add_conditional_edges(
            "ask_for_new_input",
            self.confirm_new_input,
            {
                "no_new_input": "no_new_input_requested",
                "present_new_input": "perform_input_parser"
            }
        )

        workflow.add_conditional_edges(
            "perform_input_parser",
            self.which_operation,
            {
                "alter_macrocycle": "retrieve_information",
                "create_new_macrocycle": "create_new_macrocycle"
            }
        )

        workflow.add_edge("retrieve_information", "delete_old_children")
        workflow.add_edge("delete_old_children", "alter_macrocycle")
        workflow.add_edge("alter_macrocycle", "get_formatted_list")
        workflow.add_edge("create_new_macrocycle", "get_formatted_list")
        workflow.add_edge("no_new_input_requested", "end_node")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)