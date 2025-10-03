from app.models import User_Weekday_Availability

from app.parent_retriever_agents.base_sub_agents.with_availability import BaseAgentWithAvailability as BaseAgent

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
    sub_agent_title = "Workout"

    # Retrieve User's Availability.
    def parent_retriever_agent(self, state: AgentState):
        user_id = state["user_id"]
        user_workout_day = state["user_phase_component"]
        return {"user_availability": retrieve_parent_for_day(user_id, user_workout_day["weekday_id"])}

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)