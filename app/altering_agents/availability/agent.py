from logging_config import LogAlteringAgent

from langgraph.graph import StateGraph, START, END

from app.db_session import session_scope
from app.models import User_Weekday_Availability, User_Workout_Days
from app.utils.common_table_queries import current_microcycle

from app.agent_states.availability import AgentState
from app.impact_goal_models import AvailabilityGoal
from app.goal_prompts import availability_system_prompt
from app.schedule_printers import AvailabilitySchedulePrinter

from app.altering_agents.base_sub_agents.without_parents import BaseAgentWithoutParents as BaseAgent
from app.altering_agents.base_sub_agents.without_parents import confirm_new_input
from app.edit_agents import create_availability_edit_agent
from app.solver_agents.weekday_availability import create_weekday_availability_extraction_graph

from .actions import retrieve_weekday_types, initialize_user_availability, update_user_availability

# ----------------------------------------- User Availability -----------------------------------------

class AlteringAgent(BaseAgent):
    focus = "availability"
    sub_agent_title = "Weekday Availability"
    focus_system_prompt = availability_system_prompt
    focus_goal = AvailabilityGoal
    focus_edit_agent = create_availability_edit_agent()
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
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("operation_is_alter", self.chained_conditional_inbetween)
        workflow.add_node("ask_for_new_input", self.ask_for_new_input)
        workflow.add_node("perform_input_parser", self.perform_input_parser)
        workflow.add_node("editor_agent", self.focus_edit_agent)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("agent_output_to_sqlalchemy_model", self.agent_output_to_sqlalchemy_model)
        workflow.add_node("no_new_input_requested", self.no_new_input_requested)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "operation_is_alter")

        # Whether there is a new goal to perform the change with.
        workflow.add_conditional_edges(
            "operation_is_alter",
            confirm_new_input, 
            {
                "no_new_input": "ask_for_new_input",                    # Request a new input to parse availability from if one isn't present.
                "present_new_input": "delete_old_children"              # Delete the old children for the alteration if a goal was given.
            }
        )

        # Whether there is a new goal to perform the change with.
        workflow.add_conditional_edges(
            "ask_for_new_input",
            confirm_new_input, 
            {
                "no_new_input": "no_new_input_requested",               # Indicate that no new goal was given.
                "present_new_input": "delete_old_children"              # Delete the old children for the alteration if a goal was given.
            }
        )

        workflow.add_edge("delete_old_children", "perform_input_parser")
        workflow.add_edge("perform_input_parser", "editor_agent")
        workflow.add_edge("editor_agent", "agent_output_to_sqlalchemy_model")

        workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("no_new_input_requested", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = AlteringAgent()
    return agent.create_main_agent_graph(AgentState)