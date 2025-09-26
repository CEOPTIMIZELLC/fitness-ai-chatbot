from logging_config import LogDeletionAgent
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app.db_session import session_scope
from app.models import Equipment_Library, User_Equipment

from app.main_agent.base_sub_agents.utils import new_input_request
from app.utils.item_to_string import list_to_str_for_prompt

from app.deletion_agents.base_sub_agents.base import BaseAgent

from .actions import filter_items_by_query, delete_singular
from .goal_model import EquipmentGoal
from .prompt import EquipmentDetailsPrompt
from app.schedule_printers import EquipmentSchedulePrinter

from app.agent_states.equipment import AgentState

# Determine if more details are required for the operation to occur.
def are_more_details_needed(state: AgentState):
    LogDeletionAgent.agent_steps(f"\t---------Determine if more details are needed to continue.---------")
    if state["request_more_details"]:
        LogDeletionAgent.agent_steps(f"\t---------More details are needed.---------")
        return "need_more_details"
    LogDeletionAgent.agent_steps(f"\t---------No more details are needed.---------")
    return "enough_details"

class SubAgent(BaseAgent, EquipmentDetailsPrompt):
    details_goal = EquipmentGoal
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
        LogDeletionAgent.agent_steps(f"\t---------Retrieving All {self.sub_agent_title} Schedules---------")

        schedule_dict = filter_items_by_query(state)

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogDeletionAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Node to prepare information for altering.
    def retrieve_information(self, state):
        LogDeletionAgent.agent_steps(f"\t---------Retrieving Information for Altering---------")
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

    def system_prompt_constructor(self, schedule_dict, state):
        available_equipment = list_to_str_for_prompt(state["available_equipment"], newline=True)

        user_equipment_ids = ", \n".join(
            f"{{{{unique_id: {l_item["id"]}}}}}"
            for l_item in schedule_dict
        )

        return self.details_system_prompt_constructor(
            f"[\n{user_equipment_ids}\n]", 
            f"[\n{available_equipment}\n]", 
            equipment_id = state.get("equipment_id"), 
            equipment_measurement = state.get("equipment_measurement")
        )

    # Request the details required to continue.
    def detail_extraction(self, state, schedule_dict, user_input):
        LogDeletionAgent.verbose(f"Extract the Edits from the following message: {user_input}")

        system_prompt = self.system_prompt_constructor(schedule_dict, state)

        # Retrieve the details.
        goal_class = new_input_request(user_input, system_prompt, self.details_goal)

        new_details = {}

        unique_id = goal_class.unique_id
        equipment_id = goal_class.equipment_id
        equipment_measurement = goal_class.equipment_measurement

        if unique_id:
            new_details["item_id"] = unique_id
        if equipment_id:
            item = Equipment_Library.query.filter_by(id=equipment_id).first()
            new_details["equipment_id"] = equipment_id
            new_details["equipment_name"] = item.name
        if equipment_measurement:
            new_details["equipment_measurement"] = equipment_measurement

        return new_details

    # Node to extract the information from the initial user request.
    def initial_request_parsing(self, state):
        LogDeletionAgent.agent_steps(f"\t---------Retrieve details from initial request---------")
        user_input = state.get("equipment_detail")
        schedule_dict = filter_items_by_query(state)
        return self.detail_extraction(state, schedule_dict, user_input)

    # Delete an old piece of equipment for the user.
    def delete_old(self, state):
        LogDeletionAgent.agent_steps(f"\t---------Delete Old User {self.sub_agent_title}---------")

        schedule_dict = delete_singular(state)

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

    def detail_request_constructor(self, formatted_schedule, **kwargs):
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

        question_text = "There is more than one piece of equipment that matches the criteria. Is this correct or would you like to provide more details?"
        details_contained_text = f"You have already provided the following details: \n{details_contained}"
        details_needed_text = f"You can still provide the following details: \n{details_needed}"

        return f"{question_text}\n\n{details_contained_text}\n\n{details_needed_text}\n\nHere is the list of your equipment that match this criteria:\n{formatted_schedule}"

    # Request the details required to continue.
    def request_more_details(self, state):
        LogDeletionAgent.agent_steps(f"\t---------Requesting more details to continue---------")

        schedule_dict = filter_items_by_query(state)
        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)

        human_task = self.detail_request_constructor(
            formatted_schedule, 
            item_id = state.get("item_id"), 
            equipment_name = state.get("equipment_name"), 
            equipment_measurement = state.get("equipment_measurement")
        )
        LogDeletionAgent.system_message(human_task)

        result = interrupt({
            "task": human_task
        })

        user_input = result["user_input"]
        return self.detail_extraction(state, schedule_dict, user_input)

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("initial_request_parsing", self.initial_request_parsing)
        workflow.add_node("delete_old", self.delete_old)
        workflow.add_node("request_more_details", self.request_more_details)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "retrieve_information")
        workflow.add_edge("retrieve_information", "initial_request_parsing")
        workflow.add_edge("initial_request_parsing", "delete_old")

        # Whether more details are needed to delete the piece of equipment.
        workflow.add_conditional_edges(
            "delete_old",
            are_more_details_needed, 
            {
                "need_more_details": "request_more_details",            # Request more details if needed.
                "enough_details": "get_user_list"                       # Enough details were found to create the new entry. 
            }
        )
        workflow.add_edge("request_more_details", "delete_old")

        workflow.add_edge("get_user_list", "end_node")

        workflow.add_edge("end_node", END)

        return workflow.compile()


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)