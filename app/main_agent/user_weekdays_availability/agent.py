from app.main_agent.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.impact_goal_models.availability import AvailabilityGoal
from app.goal_prompts.availability import availability_system_prompt

from app.agent_states.availability import AgentState

from app.altering_agents.availability.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.availability.agent import create_main_agent_graph as create_reading_agent

# ----------------------------------------- User Availability -----------------------------------------

class SubAgent(BaseAgent):
    focus = "availability"
    sub_agent_title = "Weekday Availability"
    focus_system_prompt = availability_system_prompt
    focus_goal = AvailabilityGoal
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)