# Database imports.
from app.models import User_Weekday_Availability
from app.common_table_queries.availability import currently_active_item as current_weekday_availability

# Agent construction imports.
from app.agent_states.availability import AgentState
from app.reading_agents.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.schedule_printers.availability import AvailabilitySchedulePrinter

# ----------------------------------------- User Availability -----------------------------------------

class SubAgent(BaseAgent):
    focus = "availability"
    sub_agent_title = "Weekday Availability"
    schedule_printer_class = AvailabilitySchedulePrinter()

    def user_list_query(self, user_id):
        return (
            User_Weekday_Availability.query
            .filter_by(user_id=user_id)
            .order_by(User_Weekday_Availability.weekday_id.asc())
            .all()
        )

    def focus_retriever_agent(self, user_id):
        return current_weekday_availability(user_id)

    def focus_list_retriever_agent(self, user_id):
        return (
            User_Weekday_Availability.query
            .filter_by(user_id=user_id)
            .order_by(User_Weekday_Availability.weekday_id.asc())
            .all()
        )


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)