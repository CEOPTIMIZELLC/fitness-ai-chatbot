from logging_config import LogMainSubAgent
from langgraph.graph import StateGraph, START, END

from app.models import User_Equipment

from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.base import BaseAgent, confirm_impact, determine_operation, determine_read_operation

from .actions import filter_items_by_query
from app.schedule_printers import EquipmentSchedulePrinter

class AgentState(MainAgentState):
    focus_name: str

    item_id: int
    equipment_id: int
    equipment_measurement: int

class SubAgent(BaseAgent):
    focus = "equipment"
    sub_agent_title = "Equipment"
    schedule_printer_class = EquipmentSchedulePrinter()

    def focus_list_retriever_agent(self, user_id):
        return (
            User_Equipment.query
            .filter_by(user_id=user_id)
            .order_by(User_Equipment.equipment_id.asc())
            .all()
        )

    # Print output.
    def get_user_list(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving All {self.sub_agent_title} Schedules---------")

        schedule_dict = filter_items_by_query(state)

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("get_user_list", self.get_user_list)
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
            determine_operation, 
            {
                "read": "operation_is_read",                            # In between step for if the operation is read.
                "alter": "end_node"                                     # In between step for if the operation is alter.
            }
        )
    
        # Whether the read operations is for a single element or plural elements.
        workflow.add_conditional_edges(
            "operation_is_read",
            determine_read_operation, 
            {
                "plural": "get_user_list",                              # Read the current schedule.
                "singular": "get_user_list"                             # Read the current element.
            }
        )

        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)


