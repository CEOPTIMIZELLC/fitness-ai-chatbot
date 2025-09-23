from logging_config import LogMainSubAgent
from langgraph.graph import StateGraph, START, END

from app.db_session import session_scope
from app.models import Equipment_Library, User_Equipment

from app.main_agent.base_sub_agents.base import BaseAgent, confirm_impact, determine_if_delete, determine_if_alter, determine_if_read, determine_read_operation

from .agent_state import AgentState
from .actions import filter_items_by_query
from .creation_agent import create_creation_agent
from .altering_agent import create_altering_agent
from .deletion_agent import create_deletion_agent
from app.schedule_printers import EquipmentSchedulePrinter

# Determine whether the outcome is to read the entire schedule or simply the current item.
def which_operation(state: AgentState):
    LogMainSubAgent.agent_steps(f"\t---------Determine if the objective is to create a new piece of equipment or alter an old one.---------")
    if state["equipment_alter_old"]:
        return "alter"
    return "create"

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

    # Node to prepare information for altering.
    def operation_is_alter(self, state):
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
        creation_agent = create_creation_agent()
        altering_agent = create_altering_agent()
        deletion_agent = create_deletion_agent()

        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_delete", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_alter", self.operation_is_alter)
        workflow.add_node("operation_is_delete", self.operation_is_alter)
        workflow.add_node("create_new", creation_agent)
        workflow.add_node("alter_old", altering_agent)
        workflow.add_node("delete_old", deletion_agent)
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
            determine_if_delete, 
            {
                "deletion": "operation_is_delete",                      # In between step for if the operation is delete.
                "not_deletion": "operation_is_not_delete"               # In between step for if the operation is not delete.
            }
        )
        workflow.add_edge("operation_is_delete", "delete_old")

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "operation_is_not_delete",
            determine_if_alter, 
            {
                "not_alter": "operation_is_not_alter",                  # In between step for if the operation is not alter.
                "alter": "operation_is_alter"                           # In between step for if the operation is alter.
            }
        )

        # Whether the goal is to read user elements.
        workflow.add_conditional_edges(
            "operation_is_not_alter",
            determine_if_read, 
            {
                "not_read": "end_node",                                 # End subagent if nothing is requested.
                "read": "operation_is_read"                             # In between step for if the operation is read.
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

        # Whether the goal is to create a new item or alter an old one.
        workflow.add_conditional_edges(
            "operation_is_alter",
            which_operation, 
            {
                "create": "create_new",                                 # Create a new item.
                "alter": "alter_old"                                    # Alter an old item. 
            }
        )

        workflow.add_edge("create_new", "get_user_list")
        workflow.add_edge("alter_old", "get_user_list")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)


