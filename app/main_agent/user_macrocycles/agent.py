from logging_config import LogMainSubAgent

from langgraph.graph import StateGraph, START, END

from app import db
from app.solver_agents.goals import create_goal_classification_graph
from app.db_session import session_scope
from app.models import Goal_Library, User_Macrocycles, User_Mesocycles
from app.utils.common_table_queries import current_macrocycle

from app.main_agent.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.main_agent.base_sub_agents.base import confirm_impact, determine_if_alter, determine_if_read, determine_read_operation
from app.main_agent.base_sub_agents.without_parents import confirm_if_performing_by_id, confirm_new_input
from app.impact_goal_models import MacrocycleGoal
from app.goal_prompts import macrocycle_system_prompt
from app.edit_agents import create_macrocycle_edit_agent

from .actions import retrieve_goal_types
from app.schedule_printers import MacrocycleSchedulePrinter

from app.agent_states.macrocycles import AgentState

from app.altering_agents.macrocycles.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.macrocycles.agent import create_main_agent_graph as create_reading_agent

# ----------------------------------------- User Macrocycles -----------------------------------------

# Determine whether the current macrocycle should be edited or if a new one should be created.
def which_operation(state: AgentState):
    LogMainSubAgent.agent_steps(f"\t---------Determine whether goal should be new---------")
    if state["macrocycle_alter_old"] and state["user_macrocycle"]:
        return "alter_old_macrocycle"
    return "create_new_macrocycle"

class SubAgent(BaseAgent):
    focus = "macrocycle"
    sub_agent_title = "Macrocycle"
    focus_system_prompt = macrocycle_system_prompt
    focus_goal = MacrocycleGoal
    focus_edit_agent = create_macrocycle_edit_agent()
    schedule_printer_class = MacrocycleSchedulePrinter()
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

    def user_list_query(self, user_id):
        return User_Macrocycles.query.filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    def focus_list_retriever_agent(self, user_id):
        return [current_macrocycle(user_id)]

    # Classify the new goal in one of the possible goal types.
    def perform_input_parser(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Perform {self.sub_agent_title} Classifier---------")
        new_goal = state["macrocycle_detail"]

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

    # Creates the new macrocycle of the determined type.
    def create_new_macrocycle(self, state: AgentState):
        user_id = state["user_id"]
        goal_id = state["goal_id"]
        new_goal = state["macrocycle_detail"]
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
        new_goal = state["macrocycle_detail"]
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
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("altering_agent", self.altering_agent)
        workflow.add_node("reading_agent", self.reading_agent)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            confirm_impact, 
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "impact_confirmed"                            # In between step for if an impact is indicated.
            }
        )

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "impact_confirmed",
            determine_if_alter, 
            {
                "not_alter": "operation_is_not_alter",                  # In between step for if the operation is not alter.
                "alter": "altering_agent"                               # Start altering subagent.
            }
        )

        # Whether the goal is to read user elements.
        workflow.add_conditional_edges(
            "operation_is_not_alter",
            determine_if_read, 
            {
                "not_read": "end_node",                                 # End subagent if nothing is requested.
                "read": "reading_agent"                                 # Start reading subagent.
            }
        )

        workflow.add_edge("altering_agent", "end_node")
        workflow.add_edge("reading_agent", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)