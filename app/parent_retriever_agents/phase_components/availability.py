from app.models import Weekday_Library, User_Weekday_Availability

from app.parent_retriever_agents.base_sub_agents.with_availability import BaseAgentWithAvailability as BaseAgent

from app.agent_states.phase_components import AgentState

# ----------------------------------------- User Workout Days -----------------------------------------

def retrieve_parent_for_week(user_id):
    availability = (
        User_Weekday_Availability.query
        .join(Weekday_Library)
        .filter(User_Weekday_Availability.user_id == user_id)
        .order_by(User_Weekday_Availability.weekday_id.asc())
        .all())
    return availability

class SubAgent(BaseAgent):
    focus = "phase_component"
    sub_agent_title = "Phase Component"

    # Retrieve User's Availability.
    def parent_retriever_agent(self, state: AgentState):
        user_id = state["user_id"]
        user_availability = retrieve_parent_for_week(user_id)

        # Convert to list of dictionaries.
        return {"user_availability": [availability.to_dict() for availability in user_availability]}

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)