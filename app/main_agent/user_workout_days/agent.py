from langgraph.graph import StateGraph, START, END

from app.models import Weekday_Library, User_Weekday_Availability
from app.utils.common_table_queries import current_microcycle

from app.main_agent.base_sub_agents.with_availability import BaseAgentWithAvailability as BaseAgent
from app.main_agent.base_sub_agents.base import confirm_impact, determine_if_alter, determine_if_read
from app.main_agent.base_sub_agents.with_parents import confirm_parent, confirm_permission
from app.main_agent.base_sub_agents.with_availability import confirm_availability, confirm_availability_permission
from app.main_agent.user_microcycles import create_microcycle_agent
from app.impact_goal_models import MicrocycleGoal
from app.goal_prompts import microcycle_system_prompt

from app.agent_states.phase_components import AgentState

from app.altering_agents.phase_components.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.phase_components.agent import create_main_agent_graph as create_reading_agent

# ----------------------------------------- User Workout Days -----------------------------------------

def retrieve_availability_for_week(user_id):
    availability = (
        User_Weekday_Availability.query
        .join(Weekday_Library)
        .filter(User_Weekday_Availability.user_id == user_id)
        .order_by(User_Weekday_Availability.weekday_id.asc())
        .all())
    return availability

class SubAgent(BaseAgent):
    focus = "phase_component"
    parent = "microcycle"
    sub_agent_title = "Phase Component"
    parent_title = "Microcycle"
    parent_system_prompt = microcycle_system_prompt
    parent_goal = MicrocycleGoal
    parent_scheduler_agent = create_microcycle_agent()
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

    def parent_retriever_agent(self, user_id):
        return current_microcycle(user_id)

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        parent_db_entry = self.parent_retriever_agent(user_id)
        parent_db_entry.mesocycles.phase_id = new_parent_id
        return parent_db_entry

    # Retrieve User's Availability.
    def availability_retriever_agent(self, state: AgentState):
        user_id = state["user_id"]
        user_availability = retrieve_availability_for_week(user_id)

        # Convert to list of dictionaries.
        return {"user_availability": [availability.to_dict() for availability in user_availability]}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_availability", self.retrieve_availability)
        workflow.add_node("ask_for_availability_permission", self.ask_for_availability_permission)
        workflow.add_node("availability_requests_extraction", self.availability_requests_extraction)
        workflow.add_node("availability_permission_denied", self.availability_permission_denied)
        workflow.add_node("availability", self.availability_node)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("ask_for_permission", self.ask_for_permission)
        workflow.add_node("parent_requests_extraction", self.parent_requests_extraction)
        workflow.add_node("permission_denied", self.permission_denied)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
        workflow.add_node("parent_retrieved", self.parent_retrieved)
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
                "impact": "retrieve_availability"                       # Retreive the availability for the alteration.
            }
        )

        # Whether an availability for the user exists.
        workflow.add_conditional_edges(
            "retrieve_availability",
            confirm_availability, 
            {
                "no_availability": "ask_for_availability_permission",   # No parent element exists.
                "availability": "retrieve_parent"                       # Retrieve the parent element if an availability is found.
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
        workflow.add_edge("availability", "retrieve_availability")

        # Whether a parent element exists.
        workflow.add_conditional_edges(
            "retrieve_parent",
            confirm_parent, 
            {
                "no_parent": "ask_for_permission",                      # No parent element exists.
                "parent": "parent_retrieved"                            # In between step for if a parent element exists.
            }
        )

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "parent_retrieved",
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