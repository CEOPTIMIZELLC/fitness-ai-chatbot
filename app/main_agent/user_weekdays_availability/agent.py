from logging_config import LogMainSubAgent
from datetime import timedelta

from langgraph.graph import StateGraph, START, END

from app import db
from app.solver_agents.weekday_availability import create_weekday_availability_extraction_graph
from app.db_session import session_scope
from app.models import User_Weekday_Availability, User_Workout_Days
from app.utils.common_table_queries import current_weekday_availability, current_microcycle

from app.main_agent.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.main_agent.base_sub_agents.base import confirm_impact, determine_if_alter, determine_if_read, determine_read_operation
from app.main_agent.base_sub_agents.without_parents import confirm_new_input
from app.impact_goal_models import AvailabilityGoal
from app.goal_prompts import availability_system_prompt
from app.edit_agents import create_availability_edit_agent

from .actions import retrieve_weekday_types, initialize_user_availability, update_user_availability
from app.schedule_printers import AvailabilitySchedulePrinter

from app.agent_states.availability import AgentState

from app.altering_agents.availability.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.availability.agent import create_main_agent_graph as create_reading_agent

# ----------------------------------------- User Availability -----------------------------------------

class SubAgent(BaseAgent):
    focus = "availability"
    sub_agent_title = "Weekday Availability"
    focus_system_prompt = availability_system_prompt
    focus_goal = AvailabilityGoal
    focus_edit_agent = create_availability_edit_agent()
    schedule_printer_class = AvailabilitySchedulePrinter()
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

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

    # Classify the new goal in one of the possible goal types.
    def perform_input_parser(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Perform {self.sub_agent_title} Parsing---------")
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
        LogMainSubAgent.agent_steps(f"\t---------Convert schedule to SQLAlchemy models.---------")
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
        LogMainSubAgent.agent_steps(f"\t---------Delete old items of current Weekday Availability---------")
        user_id = state["user_id"]
        user_microcycle = current_microcycle(user_id)
        if user_microcycle:
            microcycle_id = user_microcycle.id

            with session_scope() as s:
                s.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
            LogMainSubAgent.verbose("Successfully deleted")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("altering_agent", self.altering_agent)
        workflow.add_node("reading_agent", self.reading_agent)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            confirm_impact, 
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "impact_confirmed"                            # In between step for if an impact is indicated.
            }
        )

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "impact_confirmed",
            determine_if_alter, 
            {
                "not_alter": "operation_is_not_alter",                  # In between step for if the operation is not alter.
                "alter": "altering_agent"                               # Start altering subagent.
            }
        )

        # Whether the goal is to read user elements.
        workflow.add_conditional_edges(
            "operation_is_not_alter",
            determine_if_read, 
            {
                "not_read": "end_node",                                 # End subagent if nothing is requested.
                "read": "reading_agent"                                 # Start reading subagent.
            }
        )    

        workflow.add_edge("altering_agent", "end_node")
        workflow.add_edge("reading_agent", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)