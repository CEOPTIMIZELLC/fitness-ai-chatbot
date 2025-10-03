from app.models import User_Weekday_Availability
from app.utils.common_table_queries import current_workout_day

from app.parent_retriever_agents.base_sub_agents.base import BaseAgent
from app.main_agent.user_workout_days import create_microcycle_scheduler_agent
from app.impact_goal_models.phase_components import PhaseComponentGoal
from app.goal_prompts.phase_components import phase_component_system_prompt

from app.agent_states.workout_schedule import AgentState

# ----------------------------------------- User Workout Exercises -----------------------------------------

def retrieve_parent_for_day(user_id, weekday_id):
    # Retrieve availability for day.
    availability = (
        User_Weekday_Availability.query
        .filter_by(user_id=user_id, weekday_id=weekday_id)
        .first())
    if availability:
        return int(availability.availability.total_seconds())
    return None

class SubAgent(BaseAgent):
    focus = "workout_schedule"
    parent = "phase_component"
    sub_agent_title = "User Workout"
    parent_title = "Phase Component"
    parent_system_prompt = phase_component_system_prompt
    parent_goal = PhaseComponentGoal
    parent_scheduler_agent = create_microcycle_scheduler_agent()

    def parent_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    # In between node for when the parent is retrieved.
    def parent_retrieved(self, state: AgentState):
        return {}

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)