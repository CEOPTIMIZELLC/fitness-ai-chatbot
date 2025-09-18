from logging_config import LogMainSubAgent
from langgraph.graph import StateGraph, START, END

from app.db_session import session_scope
from app.models import User_Equipment

from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agents.base import BaseAgent, confirm_impact, determine_operation, determine_read_operation

from .actions import create_singular, filter_items_by_query, alter_singular
from app.schedule_printers import EquipmentSchedulePrinter

class AgentState(MainAgentState):
    focus_name: str

    item_id: int
    equipment_id: int
    equipment_measurement: int
    new_equipment_id: int
    new_equipment_measurement: int

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

    # Create a new piece of equipment for the user.
    def create_new(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Creating New {self.sub_agent_title} for User---------")

        schedule_dict = create_singular(state)    

        # Edit was successful if the created entry is returned.
        if schedule_dict:
            return {
                "user_equipment": schedule_dict, 
                "item_id": schedule_dict["id"], 
                "request_more_details": False
            }
        
        # If no entry was returned, then the creation requires more details
        return {"request_more_details": True}
        
    # Alter an old piece of equipment for the user.
    def alter_old(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Alter Old User {self.sub_agent_title}---------")

        schedule_dict = alter_singular(state)

        # Edit was successful if only one item was present.
        if len(schedule_dict) == 1:
            return {
                "user_equipment": schedule_dict, 
                "item_id": schedule_dict[0]["id"], 
                "request_more_details": False, 
            }
        
        # More details are required to filter the information.
        return {
            "user_equipment": schedule_dict, 
            "request_more_details": True, 
        }

    # Request the details required to continue.
    def request_more_details(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Requesting more details to continue---------")
        return {}


    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("impact_confirmed", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("operation_is_alter", self.chained_conditional_inbetween)
        workflow.add_node("create_new", self.create_new)
        workflow.add_node("alter_old", self.alter_old)
        workflow.add_node("request_more_details", self.request_more_details)
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
                "alter": "operation_is_alter"                           # In between step for if the operation is alter.
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
                "create": "create_new",                                 # Create a new piece of equipment.
                "alter": "alter_old"                                    # Alter an old piece of equipment. 
            }
        )

        # Whether more details are needed to create the new piece of equipment.
        workflow.add_conditional_edges(
            "create_new",
            are_more_details_needed, 
            {
                "need_more_details": "request_more_details",            # Request more details if needed.
                "enough_details": "get_user_list"                       # Enough details were found to create the new entry. 
            }
        )

        # Whether more details are needed to create the new piece of equipment.
        workflow.add_conditional_edges(
            "alter_old",
            are_more_details_needed, 
            {
                "need_more_details": "request_more_details",            # Request more details if needed.
                "enough_details": "get_user_list"                       # Enough details were found to create the new entry. 
            }
        )

        workflow.add_edge("request_more_details", "get_user_list")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)


