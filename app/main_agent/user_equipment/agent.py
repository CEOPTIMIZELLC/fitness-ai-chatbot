from logging_config import LogMainSubAgent
from langgraph.graph import StateGraph, START, END

from app.db_session import session_scope
from app.models import Equipment_Library, User_Equipment

from app.main_agent.base_sub_agents.base import BaseAgent, confirm_impact, determine_if_delete, determine_if_alter, determine_if_read

from .deletion_agent import create_deletion_agent
from app.schedule_printers import EquipmentSchedulePrinter

from app.agent_states.equipment import AgentState

from app.altering_agents.equipment.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.equipment.agent import create_main_agent_graph as create_reading_agent

# Determine if more details are required for the operation to occur.
def are_more_details_needed(state: AgentState):
    LogMainSubAgent.agent_steps(f"\t---------Determine if more details are needed to continue.---------")
    if state["request_more_details"]:
        LogMainSubAgent.agent_steps(f"\t---------More details are needed.---------")
        return "need_more_details"
    LogMainSubAgent.agent_steps(f"\t---------No more details are needed.---------")
    return "enough_details"

class SubAgent(BaseAgent):
    focus = "equipment"
    sub_agent_title = "Equipment"
    schedule_printer_class = EquipmentSchedulePrinter()
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

    def focus_list_retriever_agent(self, user_id):
        return (
            User_Equipment.query
            .filter_by(user_id=user_id)
            .order_by(User_Equipment.equipment_id.asc())
            .all()
        )

    # Node to prepare information for altering.
    def retrieve_information(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for Altering---------")
        items = Equipment_Library.query.all()

        # Create the list of available equipment for the LLM to choose from.
        equipment_list = [
            {
                "id": item.id, 
                "equipment_name": item.name
            } for item in items
        ]

        return {
            "available_equipment": equipment_list
        }

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        deletion_agent = create_deletion_agent()

        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_delete", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("altering_agent", self.altering_agent)
        workflow.add_node("reading_agent", self.reading_agent)
        workflow.add_node("delete_old", deletion_agent)
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

        # Whether the goal is to read or alter user elements.
        workflow.add_conditional_edges(
            "impact_confirmed",
            determine_if_delete, 
            {
                "deletion": "retrieve_information",                      # In between step for if the operation is delete.
                "not_deletion": "operation_is_not_delete"               # In between step for if the operation is not delete.
            }
        )
        workflow.add_edge("retrieve_information", "delete_old")

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "operation_is_not_delete",
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
        workflow.add_edge("delete_old", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)