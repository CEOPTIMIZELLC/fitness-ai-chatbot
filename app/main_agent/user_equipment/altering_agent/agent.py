from logging_config import LogMainSubAgent
from langgraph.graph import StateGraph, START, END

from app.main_agent.base_sub_agents.utils import sub_agent_focused_items

from ..agent_state import AgentState
from ..actions import filter_items_by_query, alter_singular
from app.schedule_printers import EquipmentSchedulePrinter


# Determine if more details are required for the operation to occur.
def are_more_details_needed(state: AgentState):
    LogMainSubAgent.agent_steps(f"\t---------Determine if more details are needed to continue.---------")
    if state["request_more_details"]:
        LogMainSubAgent.agent_steps(f"\t---------More details are needed.---------")
        return "need_more_details"
    LogMainSubAgent.agent_steps(f"\t---------No more details are needed.---------")
    return "enough_details"

class SubAgent:
    focus = "equipment"
    sub_agent_title = "Equipment"
    schedule_printer_class = EquipmentSchedulePrinter()

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)

    # Node to declare that the sub agent has ended.
    def start_node(self, state):
        LogMainSubAgent.agent_introductions(f"=========Starting {self.sub_agent_title} Alteration SubAgent=========\n")
        return {}

    # Print output.
    def get_user_list(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving All {self.sub_agent_title} Schedules---------")

        schedule_dict = filter_items_by_query(state)

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogMainSubAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}
        
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

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogMainSubAgent.agent_introductions(f"=========Ending {self.sub_agent_title} Alteration SubAgent=========\n")
        return {}


    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("alter_old", self.alter_old)
        workflow.add_node("request_more_details", self.request_more_details)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "alter_old")

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


