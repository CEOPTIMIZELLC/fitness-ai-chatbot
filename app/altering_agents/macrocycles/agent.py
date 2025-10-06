from logging_config import LogAlteringAgent
from flask import abort

# Database imports.
from app.db_session import session_scope
from app.models import User_Macrocycles, User_Mesocycles
from app.common_table_queries.macrocycles import currently_active_item as current_macrocycle

# Agent construction imports.
from app.altering_agents.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.agent_states.macrocycles import AgentState
from app.goal_prompts.macrocycles import macrocycle_system_prompt
from app.impact_goal_models.macrocycles import MacrocycleGoal
from app.schedule_printers.macrocycles import MacrocycleSchedulePrinter

# Sub agent imports.
from app.edit_agents.macrocycles import create_editing_agent
from app.solver_agents.goals import create_goal_classification_graph

# Local imports.
from .actions import retrieve_goal_types

# ----------------------------------------- User Macrocycles -----------------------------------------

class AlteringAgent(BaseAgent):
    focus = "macrocycle"
    sub_agent_title = "Macrocycle"
    focus_system_prompt = macrocycle_system_prompt
    focus_goal = MacrocycleGoal
    focus_edit_agent = create_editing_agent()
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
        if not user_macrocycle:
            abort(404, description=f"No active {self.sub_agent_title} for altering.")

        # Invoke with new macrocycle and possible goal types.
        goal = goal_app.invoke({
            "new_goal": new_goal, 
            "goal_types": goal_types, 
            "attempts": 0})
        
        return {
            "macrocycle_id": user_macrocycle.id, 
            "start_date": user_macrocycle.start_date, 
            "end_date": user_macrocycle.end_date, 
            "goal_id": goal["goal_id"]
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
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
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
def create_main_agent_graph():
    agent = AlteringAgent()
    return agent.create_main_agent_graph(AgentState)