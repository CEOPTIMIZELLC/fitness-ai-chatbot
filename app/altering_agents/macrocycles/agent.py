from logging_config import LogAlteringAgent

from langgraph.graph import StateGraph, START, END

from app.db_session import session_scope
from app.models import User_Macrocycles, User_Mesocycles
from app.utils.common_table_queries import current_macrocycle

from app.agent_states.macrocycles import AgentState
from app.goal_prompts.macrocycles import macrocycle_system_prompt
from app.impact_goal_models.macrocycles import MacrocycleGoal
from app.schedule_printers import MacrocycleSchedulePrinter

from app.altering_agents.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.altering_agents.base_sub_agents.without_parents import confirm_new_input
from app.edit_agents.macrocycles import create_main_agent_graph as create_macrocycle_edit_agent
from app.solver_agents.goals import create_goal_classification_graph

from .actions import retrieve_goal_types

# ----------------------------------------- User Macrocycles -----------------------------------------

# Determine whether the current macrocycle should be edited or if a new one should be created.
def which_operation(state: AgentState):
    LogAlteringAgent.agent_steps(f"\t---------Determine whether goal should be new---------")
    if state["macrocycle_alter_old"] and state["user_macrocycle"]:
        return "alter_old_macrocycle"
    return "create_new_macrocycle"

class AlteringAgent(BaseAgent):
    focus = "macrocycle"
    sub_agent_title = "Macrocycle"
    focus_system_prompt = macrocycle_system_prompt
    focus_goal = MacrocycleGoal
    focus_edit_agent = create_macrocycle_edit_agent()
    schedule_printer_class = MacrocycleSchedulePrinter()

    def focus_list_retriever_agent(self, user_id):
        return [current_macrocycle(user_id)]

    # Classify the new goal in one of the possible goal types.
    def perform_input_parser(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Perform {self.sub_agent_title} Classifier---------")
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
        LogAlteringAgent.agent_steps(f"\t---------Retrieving Information for Macrocycle Changing---------")
        user_macrocycle = state["user_macrocycle"]
        return {
            "macrocycle_id": user_macrocycle["id"], 
            "start_date": user_macrocycle["start_date"], 
            "end_date": user_macrocycle["end_date"], 
        }

    # Delete the old children belonging to the current item.
    def delete_old_children(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Delete old items of current Macrocycle---------")
        macrocycle_id = state["macrocycle_id"]
        with session_scope() as s:
            s.query(User_Mesocycles).filter_by(macrocycle_id=macrocycle_id).delete()
        LogAlteringAgent.verbose("Successfully deleted")
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
        workflow.add_node("operation_is_alter", self.chained_conditional_inbetween)
        workflow.add_node("ask_for_new_input", self.ask_for_new_input)
        workflow.add_node("perform_input_parser", self.perform_input_parser)
        workflow.add_node("create_new_macrocycle", self.create_new_macrocycle)
        workflow.add_node("editor_agent_for_creation", self.focus_edit_agent)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("editor_agent_for_alteration", self.focus_edit_agent)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("alter_old_macrocycle", self.alter_old_macrocycle)
        workflow.add_node("no_new_input_requested", self.no_new_input_requested)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "operation_is_alter")

        # Whether there is a new goal to perform the change with.
        workflow.add_conditional_edges(
            "operation_is_alter",
            confirm_new_input, 
            {
                "no_new_input": "ask_for_new_input",                    # Request a new macrocycle goal if one isn't present.
                "present_new_input": "perform_input_parser"             # Parse the goal for what category it falls into if one is present.
            }
        )

        # Whether there is a new goal to perform the change with.
        workflow.add_conditional_edges(
            "ask_for_new_input",
            confirm_new_input, 
            {
                "no_new_input": "no_new_input_requested",               # Indicate that no new goal was given.
                "present_new_input": "perform_input_parser"             # Parse the goal for what category it falls into if one is present.
            }
        )

        # Whether the intention is to alter the current macrocycle or to create a new one.
        workflow.add_conditional_edges(
            "perform_input_parser",
            which_operation,
            {
                "alter_old_macrocycle": "retrieve_information",             # Alter the current macrocycle.
                "create_new_macrocycle": "editor_agent_for_creation"        # Create a new macrocycle.
            }
        )

        workflow.add_edge("editor_agent_for_creation", "create_new_macrocycle")

        workflow.add_edge("retrieve_information", "editor_agent_for_alteration")
        workflow.add_edge("editor_agent_for_alteration", "delete_old_children")
        workflow.add_edge("delete_old_children", "alter_old_macrocycle")
        workflow.add_edge("alter_old_macrocycle", "get_formatted_list")
        workflow.add_edge("create_new_macrocycle", "get_formatted_list")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("no_new_input_requested", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = AlteringAgent()
    return agent.create_main_agent_graph(AgentState)