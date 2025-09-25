from logging_config import LogMainSubAgent
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app.models import Equipment_Library

from app.main_agent.base_sub_agents.utils import sub_agent_focused_items, new_input_request
from app.utils.item_to_string import list_to_str_for_prompt

from .actions import create_singular
from .goal_model import EquipmentGoal
from .prompt import EquipmentDetailsPrompt
from app.schedule_printers import EquipmentSchedulePrinter

from app.agent_states.equipment import AgentState

# Determine if more details are required for the operation to occur.
def are_more_details_needed(state: AgentState):
    LogMainSubAgent.agent_steps(f"\t---------Determine if more details are needed to continue.---------")
    if state["request_more_details"]:
        LogMainSubAgent.agent_steps(f"\t---------More details are needed.---------")
        return "need_more_details"
    LogMainSubAgent.agent_steps(f"\t---------No more details are needed.---------")
    return "enough_details"

class SubAgent(EquipmentDetailsPrompt):
    details_goal = EquipmentGoal
    focus = "equipment"
    sub_agent_title = "Equipment"
    schedule_printer_class = EquipmentSchedulePrinter()

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)

    # Node to declare that the sub agent has ended.
    def start_node(self, state):
        LogMainSubAgent.agent_introductions(f"=========Starting {self.sub_agent_title} Creation SubAgent=========\n")
        return {}

    def system_prompt_constructor(self, state):
        available_equipment = list_to_str_for_prompt(state["available_equipment"], newline=True)
        return self.details_system_prompt_constructor(
            f"[\n{available_equipment}\n]", 
            equipment_id = state.get("equipment_id"), 
            equipment_measurement = state.get("equipment_measurement")
        )

    # Request the details required to continue.
    def detail_extraction(self, state, user_input):
        LogMainSubAgent.verbose(f"Extract the Edits from the following message: {user_input}")

        system_prompt = self.system_prompt_constructor(state)

        # Retrieve the details.
        goal_class = new_input_request(user_input, system_prompt, self.details_goal)

        new_details = {}

        equipment_id = goal_class.equipment_id

        if equipment_id:
            item = Equipment_Library.query.filter_by(id=equipment_id).first()
            new_details["equipment_id"] = equipment_id
            new_details["equipment_name"] = item.name
        if goal_class.equipment_measurement:
            new_details["equipment_measurement"] = goal_class.equipment_measurement

        return new_details

    # Node to extract the information from the initial user request.
    def initial_request_parsing(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Retrieve details from initial request---------")
        user_input = state.get("equipment_detail")
        return self.detail_extraction(state, user_input)

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

    def detail_request_constructor(self, **kwargs):
        details_contained = ", ".join(
            f"{key}: {value}"
            for key, value in kwargs.items()
            if value != None
        )

        details_needed = ", ".join(
            f"{key}"
            for key, value in kwargs.items()
            if value == None
        )

        return f"I still need your desired {details_needed} to add this piece of equipment.\nAs of right now, I have the following details\n{details_contained}"

    # Request the details required to continue.
    def request_more_details(self, state):
        LogMainSubAgent.agent_steps(f"\t---------Requesting more details to continue---------")

        human_task = self.detail_request_constructor(
            equipment_id = state.get("equipment_id"), 
            equipment_name = state.get("equipment_name"), 
            equipment_measurement = state.get("equipment_measurement")
        )
        LogMainSubAgent.system_message(human_task)

        result = interrupt({
            "task": human_task
        })

        user_input = result["user_input"]
        return self.detail_extraction(state, user_input)

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogMainSubAgent.agent_introductions(f"=========Ending {self.sub_agent_title} Creation SubAgent=========\n")
        return {}


    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("initial_request_parsing", self.initial_request_parsing)
        workflow.add_node("create_new", self.create_new)
        workflow.add_node("request_more_details", self.request_more_details)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "initial_request_parsing")
        workflow.add_edge("initial_request_parsing", "create_new")

        # Whether more details are needed to create the new piece of equipment.
        workflow.add_conditional_edges(
            "create_new",
            are_more_details_needed, 
            {
                "need_more_details": "request_more_details",            # Request more details if needed.
                "enough_details": "end_node"                            # Enough details were found to create the new entry. 
            }
        )
        workflow.add_edge("request_more_details", "create_new")

        workflow.add_edge("end_node", END)

        return workflow.compile()


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)


