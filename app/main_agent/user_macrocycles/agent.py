from logging_config import LogMainSubAgent

from langgraph.graph import StateGraph, START, END

from app.db_session import session_scope
from app.models import User_Macrocycles

from app.main_agent.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.main_agent.base_sub_agents.base import confirm_impact, determine_if_alter, determine_if_read
from app.impact_goal_models import MacrocycleGoal
from app.goal_prompts import macrocycle_system_prompt

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
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

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