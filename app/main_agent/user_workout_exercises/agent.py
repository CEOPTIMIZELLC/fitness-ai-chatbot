from langgraph.graph import StateGraph, START, END

from app.models import User_Weekday_Availability
from app.utils.common_table_queries import current_workout_day

from app.main_agent.base_sub_agents.with_availability import BaseAgentWithAvailability as BaseAgent
from app.main_agent.base_sub_agents.base import confirm_impact, determine_if_alter, determine_if_read
from app.main_agent.base_sub_agents.with_parents import confirm_parent, confirm_permission
from app.main_agent.base_sub_agents.with_availability import confirm_availability, confirm_availability_permission
from app.main_agent.user_workout_days import create_microcycle_scheduler_agent
from app.impact_goal_models.phase_components import PhaseComponentGoal
from app.goal_prompts.phase_components import phase_component_system_prompt

from app.agent_states.workout_schedule import AgentState

from app.altering_agents.workout_schedule.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.workout_schedule.agent import create_main_agent_graph as create_reading_agent

# ----------------------------------------- User Workout Exercises -----------------------------------------

def retrieve_availability_for_day(user_id, weekday_id):
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
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

    def parent_retriever_agent(self, user_id):
        return current_workout_day(user_id)

    # Retrieve User's Availability.
    def availability_retriever_agent(self, state: AgentState):
        user_id = state["user_id"]
        user_workout_day = state["user_phase_component"]
        return {"user_availability": retrieve_availability_for_day(user_id, user_workout_day["weekday_id"])}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("extract_operations", self.extract_operations)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("ask_for_permission", self.ask_for_permission)
        workflow.add_node("parent_requests_extraction", self.parent_requests_extraction)
        workflow.add_node("permission_denied", self.permission_denied)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
        workflow.add_node("parent_retrieved", self.chained_conditional_inbetween)
        workflow.add_node("retrieve_availability", self.retrieve_availability)
        workflow.add_node("ask_for_availability_permission", self.ask_for_availability_permission)
        workflow.add_node("availability_found", self.chained_conditional_inbetween)
        workflow.add_node("availability_requests_extraction", self.availability_requests_extraction)
        workflow.add_node("availability_permission_denied", self.availability_permission_denied)
        workflow.add_node("availability", self.availability_node)
        workflow.add_node("altering_agent", self.altering_agent)
        workflow.add_node("reading_agent", self.reading_agent)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            confirm_impact, 
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "extract_operations"                          # Determine what operations to perform.
            }
        )
        workflow.add_edge("extract_operations", "retrieve_parent")

        # Whether a parent element exists.
        workflow.add_conditional_edges(
            "retrieve_parent",
            confirm_parent, 
            {
                "no_parent": "ask_for_permission",                      # No parent element exists.
                "parent": "parent_retrieved"                            # In between step for if a parent element exists.
            }
        )
        workflow.add_edge("parent_retrieved", "retrieve_availability")


        # Whether a parent element is allowed to be created where one doesn't already exist.
        workflow.add_edge("ask_for_permission", "parent_requests_extraction")
        workflow.add_conditional_edges(
            "parent_requests_extraction",
            confirm_permission, 
            {
                "permission_denied": "permission_denied",               # The agent isn't allowed to create a parent.
                "permission_granted": "parent_agent"                    # The agent is allowed to create a parent.
            }
        )
        workflow.add_edge("parent_agent", "retrieve_parent")

        # Whether an availability for the user exists.
        workflow.add_conditional_edges(
            "retrieve_availability",
            confirm_availability, 
            {
                "no_availability": "ask_for_availability_permission",   # No parent element exists.
                "availability": "availability_found"                    # Retrieve the information for the alteration.
            }
        )

        # Whether an availability for the user is allowed to be created where one doesn't already exist.
        workflow.add_edge("ask_for_availability_permission", "availability_requests_extraction")
        workflow.add_conditional_edges(
            "availability_requests_extraction",
            confirm_availability_permission, 
            {
                "permission_denied": "availability_permission_denied",  # The agent isn't allowed to create availability.
                "permission_granted": "availability"                    # The agent is allowed to create availability.
            }
        )
        workflow.add_edge("availability", "retrieve_parent")

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "availability_found",
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
        workflow.add_edge("permission_denied", "end_node")
        workflow.add_edge("availability_permission_denied", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)