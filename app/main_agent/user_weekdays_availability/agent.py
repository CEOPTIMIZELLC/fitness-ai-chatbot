from config import verbose, verbose_subagent_steps
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from app import db
from app.agents.weekday_availability import create_weekday_availability_extraction_graph
from app.models import User_Weekday_Availability, User_Workout_Days
from app.utils.common_table_queries import current_microcycle

from app.main_agent.base_sub_agents.without_parents import BaseAgent
from app.main_agent.impact_goal_models import AvailabilityGoal
from app.main_agent.prompts import availability_system_prompt

from .actions import retrieve_weekday_types

# ----------------------------------------- User Availability -----------------------------------------

class AgentState(TypedDict):
    user_id: int

    user_input: str
    attempts: int

    availability_impacted: bool
    availability_is_altered: bool
    availability_message: str
    availability_formatted: str

    agent_output: list

class SubAgent(BaseAgent):
    focus = "availability"
    sub_agent_title = "Weekday Availability"
    focus_system_prompt = availability_system_prompt
    focus_goal = AvailabilityGoal

    def user_list_query(user_id):
        return User_Weekday_Availability.query.filter_by(user_id=user_id).all()

    # Classify the new goal in one of the possible goal types.
    def perform_input_parser(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Perform {self.sub_agent_title} Parsing---------")
        new_availability = state["availability_message"]

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
        if verbose_subagent_steps:
            print(f"\t---------Convert schedule to SQLAlchemy models.---------")
        user_id = state["user_id"]
        weekday_availability = state["agent_output"]
        # Update each availability entry to the database.
        for i in weekday_availability:
            db_entry = User_Weekday_Availability(
                user_id=user_id, 
                weekday_id=i["weekday_id"], 
                availability=i["availability"])
            db.session.merge(db_entry)
        db.session.commit()
        return {}

    # Delete the old children belonging to the current item.
    def delete_old_children(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Delete old items of current Weekday Availability---------")
        user_id = state["user_id"]
        user_microcycle = current_microcycle(user_id)
        if user_microcycle:
            microcycle_id = user_microcycle.id

            db.session.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
            if verbose:
                print("Successfully deleted")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)

        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("ask_for_new_input", self.ask_for_new_input)
        workflow.add_node("perform_input_parser", self.perform_input_parser)
        workflow.add_node("delete_old_children", self.delete_old_children)
        workflow.add_node("agent_output_to_sqlalchemy_model", self.agent_output_to_sqlalchemy_model)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("no_new_input_requested", self.no_new_input_requested)
        workflow.add_node("end_node", self.end_node)

        workflow.add_conditional_edges(
            START,
            self.confirm_impact,
            {
                "no_impact": "end_node",
                "impact": "impact_confirmed"
            }
        )

        workflow.add_conditional_edges(
            "impact_confirmed",
            self.confirm_new_input,
            {
                "no_new_input": "ask_for_new_input",
                "present_new_input": "delete_old_children"
            }
        )

        workflow.add_conditional_edges(
            "ask_for_new_input",
            self.confirm_new_input,
            {
                "no_new_input": "no_new_input_requested",
                "present_new_input": "delete_old_children"
            }
        )

        workflow.add_edge("delete_old_children", "perform_input_parser")
        workflow.add_edge("perform_input_parser", "agent_output_to_sqlalchemy_model")
        workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
        workflow.add_edge("no_new_input_requested", "end_node")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)