from logging_config import LogReadingAgent
from langgraph.graph import StateGraph, START, END

from app.models import User_Equipment

from app.agent_states.equipment import AgentState
from app.reading_agents.base_sub_agents.base import BaseAgent, determine_read_operation
from app.schedule_printers import EquipmentSchedulePrinter

from .actions import filter_items_by_query

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
        LogReadingAgent.agent_steps(f"\t---------Retrieving All {self.sub_agent_title} Schedules---------")

        schedule_dict = filter_items_by_query(state)

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogReadingAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "operation_is_read")

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


