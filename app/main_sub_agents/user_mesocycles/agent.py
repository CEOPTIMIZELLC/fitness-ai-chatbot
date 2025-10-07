# Agent construction imports.
from app.main_sub_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.agent_states.mesocycles import AgentState

# Sub agent imports.
from app.creation_agents.mesocycles import create_creation_agent
from app.reading_agents.mesocycles import create_reading_agent
from app.parent_retriever_agents.mesocycles import create_parent_retriever_agent

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class SubAgent(BaseAgent):
    focus = "mesocycle"
    sub_agent_title = "Mesocycle"
    parent_scheduler_agent = create_parent_retriever_agent()
    creation_agent = create_creation_agent()
    reading_agent = create_reading_agent()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)