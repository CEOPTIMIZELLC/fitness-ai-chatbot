# Agent construction imports.
from app.main_agent.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.agent_states.availability import AgentState
from app.goal_prompts.availability import availability_system_prompt
from app.impact_goal_models.availability import AvailabilityGoal

# Sub agent imports.
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

    # Performs necessary formatting changes for the subagent before changing the state.
    def format_operations(self, state_updates):
        # Combine the alter and creation requests since they are synonamous for availability.
        if any(key in state_updates for key in ("is_alter", "is_create")):
            is_alter = state_updates.pop("is_alter", False) or state_updates.pop("is_create", False)
            
            # Combine requests.
            item_request_list = [state_updates.pop("alter_detail", None), state_updates.pop("create_detail", None)]
            alter_detail = " ".join(
                value
                for value in item_request_list
                if value != None
            )

            state_updates["is_alter"] = is_alter
            state_updates["alter_detail"] = alter_detail
        return state_updates

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)