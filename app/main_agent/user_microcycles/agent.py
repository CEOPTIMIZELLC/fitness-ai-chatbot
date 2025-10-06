# Agent construction imports.
from app.main_agent.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.agent_states.microcycles import AgentState

# Sub agent imports.
from app.altering_agents.microcycles.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.microcycles.agent import create_main_agent_graph as create_reading_agent
from app.parent_retriever_agents.microcycles.agent import create_main_agent_graph as create_parent_retriever_agent

# ----------------------------------------- User Microcycles -----------------------------------------

class SubAgent(BaseAgent):
    focus = "microcycle"
    sub_agent_title = "Microcycle"
    parent_scheduler_agent = create_parent_retriever_agent()
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)