from logging_config import LogMainSubAgent

from app.utils.common_table_queries import current_macrocycle

from app.main_agent.user_macrocycles import MacrocycleAgentNode
from app.main_agent.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.impact_goal_models.macrocycles import MacrocycleGoal
from app.goal_prompts.macrocycles import macrocycle_system_prompt

from app.agent_states.mesocycles import AgentState

from app.altering_agents.mesocycles.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.mesocycles.agent import create_main_agent_graph as create_reading_agent

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
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

    def parent_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        parent_db_entry = self.parent_retriever_agent(user_id)
        parent_db_entry.goal_id = new_parent_id
        return parent_db_entry

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        goal_class_dump = goal_class.model_dump()
        parsed_goal = {
            focus_names["is_altered"]: True,
            focus_names["read_plural"]: False,
            focus_names["read_current"]: False,
            "macrocycle_alter_old": goal_class_dump.pop("alter_old", False), 
            "other_requests": goal_class_dump.pop("other_requests", None)
        }

        # Alter the variables in the state to match those retrieved from the LLM.
        for key, value in goal_class_dump.items():
            if value is not None:
                parsed_goal[focus_names[key]] = value

        return parsed_goal

    # Request is unique for Macrocycle for Mesocycle
    def parent_requests_extraction(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\n---------Extract Other Requests---------")
        return self.other_requests_information_extractor(state, self.parent, f"{self.parent}_other_requests")

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)