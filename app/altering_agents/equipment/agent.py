from logging_config import LogAlteringAgent
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app.main_agent.base_sub_agents.utils import new_input_request
from app.utils.item_to_string import list_to_str_for_prompt

from app.db_session import session_scope
from app.models import Equipment_Library, User_Equipment

from app.altering_agents.base_sub_agents.base import BaseAgent

from .actions import extract_sub_goal_class_info, filter_items_by_query, alter_singular
from .goal_model import EquipmentGoal, EquipmentRequests
from .prompt import EquipmentDetailsPrompt
from app.schedule_printers import EquipmentSchedulePrinter

from app.agent_states.equipment import AgentState

# Determine if more details are required for the operation to occur.
def are_more_details_needed(state: AgentState):
    LogAlteringAgent.agent_steps(f"\t---------Determine if more details are needed to continue.---------")
    if state["request_more_details"]:
        LogAlteringAgent.agent_steps(f"\t---------More details are needed.---------")
        return "need_more_details"
    LogAlteringAgent.agent_steps(f"\t---------No more details are needed.---------")
    return "enough_details"

class SubAgent(BaseAgent, EquipmentDetailsPrompt):
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
        LogAlteringAgent.agent_steps(f"\t---------Retrieving All {self.sub_agent_title} Schedules---------")

        schedule_dict = filter_items_by_query(state)

        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)
        LogAlteringAgent.formatted_schedule(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    def system_prompt_constructor(self, schedule_dict, state, initial_request=False):
        available_equipment = list_to_str_for_prompt(state["available_equipment"], newline=True)

        user_equipment_ids = ", \n".join(
            f"{{{{unique_id: {l_item["id"]}}}}}"
            for l_item in schedule_dict
        )

        if initial_request:
            return self.request_system_prompt_constructor(
                f"[\n{user_equipment_ids}\n]", 
                f"[\n{available_equipment}\n]"
            )

        return self.details_system_prompt_constructor(
            f"[\n{user_equipment_ids}\n]", 
            f"[\n{available_equipment}\n]", 
            equipment_id = state.get("equipment_id"), 
            equipment_measurement = state.get("equipment_measurement")
        )

    # Node to extract the information from the initial user request.
    def initial_request_parsing(self, state):
        LogAlteringAgent.agent_steps(f"\t---------Retrieve details from initial request---------")
        user_input = state.get("equipment_detail")
        schedule_dict = filter_items_by_query(state)
        LogAlteringAgent.verbose(f"Extract the Edits from the following message: {user_input}")

        system_prompt = self.system_prompt_constructor(schedule_dict, state, initial_request=True)

        # Retrieve the details.
        goal_class = new_input_request(user_input, system_prompt, EquipmentRequests)

        new_details = {}

        if goal_class.old_equipment_information:
            new_details = extract_sub_goal_class_info(new_details, goal_class.old_equipment_information, key_name="equipment")
            old_equipment_id = goal_class.old_equipment_information.unique_id

            if old_equipment_id:
                new_details["item_id"] = old_equipment_id

        if goal_class.new_equipment_information:
            new_details = extract_sub_goal_class_info(new_details, goal_class.new_equipment_information, key_name="new_equipment")

        return new_details
        
    # Alter an old piece of equipment for the user.
    def alter_old(self, state):
        LogAlteringAgent.agent_steps(f"\t---------Alter Old User {self.sub_agent_title}---------")

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
        LogAlteringAgent.agent_steps(f"\t---------Requesting more details to continue---------")

        schedule_dict = filter_items_by_query(state)
        formatted_schedule = self.schedule_printer_class.run_printer(schedule_dict)

        human_task = self.detail_request_constructor(
            formatted_schedule, 
            item_id = state.get("item_id"), 
            equipment_name = state.get("equipment_name"), 
            equipment_measurement = state.get("equipment_measurement")
        )
        LogAlteringAgent.system_message(human_task)

        result = interrupt({
            "task": human_task
        })

        user_input = result["user_input"]
        LogAlteringAgent.verbose(f"Extract the Edits from the following message: {user_input}")

        system_prompt = self.system_prompt_constructor(schedule_dict, state)

        # Retrieve the details.
        goal_class = new_input_request(user_input, system_prompt, EquipmentGoal)

        new_details = {}
        new_details = extract_sub_goal_class_info(new_details, goal_class, key_name="equipment")

        if goal_class.unique_id:
            new_details["item_id"] = goal_class.unique_id

        return new_details

    # Node to prepare information for altering.
    def retrieve_information(self, state):
        LogAlteringAgent.agent_steps(f"\t---------Retrieving Information for Altering---------")
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
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_information", self.retrieve_information)
        workflow.add_node("initial_request_parsing", self.initial_request_parsing)
        workflow.add_node("alter_old", self.alter_old)
        workflow.add_node("request_more_details", self.request_more_details)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "retrieve_information")
        workflow.add_edge("retrieve_information", "initial_request_parsing")
        workflow.add_edge("initial_request_parsing", "alter_old")

        # Whether more details are needed to create the new piece of equipment.
        workflow.add_conditional_edges(
            "alter_old",
            are_more_details_needed, 
            {
                "need_more_details": "request_more_details",            # Request more details if needed.
                "enough_details": "get_user_list"                       # Enough details were found to create the new entry. 
            }
        )
        workflow.add_edge("request_more_details", "alter_old")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()


# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)


