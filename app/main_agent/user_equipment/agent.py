from logging_config import LogMainSubAgent
from langgraph.graph import StateGraph, START, END

from app.db_session import session_scope

from app.main_agent.base_sub_agents.base import BaseAgent, confirm_impact, determine_if_delete, determine_if_alter, determine_if_create, determine_if_read

from app.schedule_printers.equipment import EquipmentSchedulePrinter

from app.agent_states.equipment import AgentState

from app.altering_agents.equipment.agent import create_main_agent_graph as create_altering_agent
from app.creation_agents.equipment.agent import create_main_agent_graph as create_creation_agent
from app.deletion_agents.equipment.agent import create_main_agent_graph as create_deletion_agent
from app.reading_agents.equipment.agent import create_main_agent_graph as create_reading_agent

class SubAgent(BaseAgent):
    focus = "equipment"
    sub_agent_title = "Equipment"
    schedule_printer_class = EquipmentSchedulePrinter()
    altering_agent = create_altering_agent()
    creation_agent = create_creation_agent()
    deletion_agent = create_deletion_agent()
    reading_agent = create_reading_agent()

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_delete", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_create", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("deletion_agent", self.deletion_agent)
        workflow.add_node("creation_agent", self.creation_agent)
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

        # Whether the goal is to read or alter user elements.
        workflow.add_conditional_edges(
            "impact_confirmed",
            determine_if_delete, 
            {
                "not_deletion": "operation_is_not_delete",              # In between step for if the operation is not delete.
                "deletion": "deletion_agent"                            # Start deletion subagent.
            }
        )

        # Whether the goal is to create user elements.
        workflow.add_conditional_edges(
            "operation_is_not_delete",
            determine_if_create, 
            {
                "not_create": "operation_is_not_create",                # In between step for if the operation is not create.
                "create": "creation_agent"                              # Start creation subagent.
            }
        )

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "operation_is_not_create",
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

        workflow.add_edge("deletion_agent", "end_node")
        workflow.add_edge("creation_agent", "end_node")
        workflow.add_edge("altering_agent", "end_node")
        workflow.add_edge("reading_agent", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)