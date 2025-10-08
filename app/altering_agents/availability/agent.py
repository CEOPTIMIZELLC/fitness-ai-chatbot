from logging_config import LogAlteringAgent

# Database imports.
from app.db_session import session_scope
from app.models import User_Weekday_Availability, User_Workout_Days
from app.common_table_queries.microcycles import currently_active_item as current_microcycle

# Agent construction imports.
from app.altering_agents.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.agent_states.availability import AgentState
from app.goal_prompts.availability import availability_system_prompt
from app.impact_goal_models.availability import AvailabilityGoal
from app.schedule_printers.availability import AvailabilitySchedulePrinter

# Sub agent imports.
from app.edit_agents.availability import create_editing_agent
from app.solver_agents.weekday_availability import create_weekday_availability_extraction_graph

# Local imports.
from .actions import retrieve_weekday_types, initialize_user_availability, update_user_availability

# ----------------------------------------- User Availability -----------------------------------------

class AlteringAgent(BaseAgent):
    focus = "availability"
    sub_agent_title = "Weekday Availability"
    focus_system_prompt = availability_system_prompt
    focus_goal = AvailabilityGoal
    focus_edit_agent = create_editing_agent()
    schedule_printer_class = AvailabilitySchedulePrinter()

    def focus_list_retriever_agent(self, user_id):
        return (
            User_Weekday_Availability.query
            .filter_by(user_id=user_id)
            .order_by(User_Weekday_Availability.weekday_id.asc())
            .all()
        )

    # Classify the new goal in one of the possible goal types.
    def perform_input_parser(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Perform {self.sub_agent_title} Parsing---------")
        new_availability = state["availability_detail"]

        # There are only so many types a weekday can be classified as, with all of them being stored.
        weekday_types = retrieve_weekday_types()
        weekday_app = create_weekday_availability_extraction_graph()

        # Invoke with new weekday and possible weekday types.
        result = weekday_app.invoke(
            {
                "new_availability": new_availability, 
                "weekday_types": weekday_types, 
                "attempts": 0
            })
        
        return {"agent_output": result["weekday_availability"]}

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Convert schedule to SQLAlchemy models.---------")
        user_id = state["user_id"]
        weekday_availability = state["agent_output"]

        # Update each availability entry to the database.
        with session_scope() as s:
            user_availability = s.query(User_Weekday_Availability).filter_by(user_id=user_id).all()

            if len(user_availability) != 7:
                initialize_user_availability(s, user_id)

            update_user_availability(s, user_id, weekday_availability)
        return {}

    # Delete the old children belonging to the current item.
    def delete_old_children(self, state: AgentState):
        LogAlteringAgent.agent_steps(f"\t---------Delete old items of current Weekday Availability---------")
        user_id = state["user_id"]
        user_microcycle = current_microcycle(user_id)
        if user_microcycle:
            microcycle_id = user_microcycle.id

            with session_scope() as s:
                s.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
            LogAlteringAgent.verbose("Successfully deleted")
        return {}

# Create main agent.
def create_main_agent_graph():
    agent = AlteringAgent()
    return agent.create_main_agent_graph(AgentState)