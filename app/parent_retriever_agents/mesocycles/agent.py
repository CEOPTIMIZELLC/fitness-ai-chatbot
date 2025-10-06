from logging_config import LogParentSubAgent

from app.utils.agent_state_helpers import goal_classifier_parser
from app.common_table_queries.macrocycles import currently_active_item as current_macrocycle

from app.main_agent.user_macrocycles import MacrocycleAgentNode
from app.parent_retriever_agents.base_sub_agents.base import BaseAgent
from app.impact_goal_models.macrocycles import MacrocycleGoal
from app.goal_prompts.macrocycles import macrocycle_system_prompt

from app.agent_states.mesocycles import AgentState

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class SubAgent(MacrocycleAgentNode, BaseAgent):
    focus = "mesocycle"
    parent = "macrocycle"
    sub_agent_title = "Mesocycle"
    parent_title = "Macrocycle"
    parent_system_prompt = macrocycle_system_prompt
    parent_goal = MacrocycleGoal
    parent_scheduler_agent = MacrocycleAgentNode.macrocycle_node

    def parent_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        parent_db_entry = self.parent_retriever_agent(user_id)
        parent_db_entry.goal_id = new_parent_id
        return parent_db_entry

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        return goal_classifier_parser(focus_names, goal_class, f"{self.parent}_other_requests")

    # Request is unique for Macrocycle for Mesocycle
    def parent_requests_extraction(self, state: AgentState):
        LogParentSubAgent.agent_steps(f"\n---------Extract Other Requests---------")
        return self.other_requests_information_extractor(state, self.parent, f"{self.parent}_other_requests")

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)