from config import request_schedule_edits, confirm_valid_schedule, confirm_invalid_schedule
from logging_config import LogEditorAgent
import copy

from typing_extensions import TypeVar, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app.utils.item_to_string import list_to_str

from .utils import does_user_allow_schedule, new_input_request

class AgentState(TypedDict):
    is_edited: bool
    violations: list
    is_valid: bool
    allow_schedule: bool
    edits: any
    other_requests: str
    edited_schedule: list
    edited_schedule_printed: str
    agent_output: list
    schedule_printed: str

# Create a generic type variable that must be a subclass of MainAgentState
TState = TypeVar('TState', bound=AgentState)

class ScheduleFormatterMethods:
    keys_to_remove = []

    # Format the fields of the workout schedule to improve performance from the LLM.
    def format_fields_for_schedule(self, schedule_item):
        return schedule_item

    # Method to remove keys from the schedule that aren't useful for the LLM.
    def remove_unnecessary_keys_from_workout_schedule(self, schedule_list):
        for schedule_item in schedule_list:
            self.format_fields_for_schedule(schedule_item)

            # Remove all items not useful for the AI
            for key_to_remove in self.keys_to_remove:
                schedule_item.pop(key_to_remove, None)
        return schedule_list

    # Method to get the list names and ids.
    def get_ids_and_names(self, list_of_dicts):
        string_output = ", \n".join(
            f"{{{{'id': {e[self.schedule_id_key]}, '{self.schedule_name_key}': {e[self.schedule_name_key]}}}}}"
            for e in list_of_dicts
        )
        return f"[{string_output}]"

    # Method to format a dictionary element to a string.
    def dict_to_string(self, dict_item):
        string_output = ", ".join(
            f"'{key}': '{value}'" 
            for key, value in dict_item.items()
            if key != "id" and key != self.schedule_name_key
        )
        return f"'id': {dict_item["id"]}, '{self.schedule_name_key}': {dict_item[self.schedule_name_key]}, {string_output}"

    # Method to format the workout summary for the LLM.
    def list_of_dicts_to_string(self, list_of_dicts):
        string_output = ", \n".join(
            f"{{{{{self.dict_to_string(list_item)}}}}}"
            for list_item in list_of_dicts
        )
        return f"[{string_output}]"

# Confirm that the desired section should be edited.
def confirm_edits(state):
    LogEditorAgent.agent_steps(f"\t---------Confirm that the Schedule is Edited---------")
    if state["is_edited"]:
        LogEditorAgent.agent_steps(f"\t---------Is Edited---------")
        return "is_edited"
    return "not_edited"

# Confirm that the user wants to move forward with the invalid schedule.
def confirm_interest(state):
    LogEditorAgent.agent_steps(f"\t---------Confirm Interest in the Invalid Schedule---------")
    if state["allow_schedule"]:
        LogEditorAgent.agent_steps(f"\t---------Allowed the Schedule---------")
        return "allow_schedule"
    LogEditorAgent.agent_steps(f"\t---------Do NOT Allow the Schedule---------")
    return "do_not_allow_schedule"

class BaseSubAgent(ScheduleFormatterMethods):
    edit_goal = None
    list_printer_class = None

    # The key used to identify items from the original schedule.
    schedule_id_key = "id"
    schedule_name_key = "name"

    # Node to declare that the sub agent has ended.
    def start_node(self, state):
        LogEditorAgent.agent_introductions(f"=========Starting Editor SubAgent=========\n")
        return {}

    # Adds necessary keys for the formatter to the schedule item. 
    def add_necessary_keys_to_schedule_item(self, schedule_list):
        return schedule_list

    # Format the structured schedule.
    def _get_formatted_proposed_list(self, state, schedule_key, schedule_printed_key):
        schedule_list = state[schedule_key]

        # Add necessary keys for the formatter to the schedule items 
        schedule_list = self.add_necessary_keys_to_schedule_item(schedule_list)

        formatted_schedule = self.list_printer_class.run_printer(schedule_list)
        LogEditorAgent.formatted_schedule(formatted_schedule)

        return {
            schedule_key: schedule_list, 
            schedule_printed_key: formatted_schedule
        }

    # Format the structured schedule.
    def format_proposed_list(self, state: TState):
        LogEditorAgent.agent_steps(f"\t---------Format Proposed Workout Schedule---------")
        return self._get_formatted_proposed_list(state, "agent_output", "schedule_printed")

    # Create prompt to request schedule edits.
    def edit_prompt_creator(self, schedule_list_original, schedule_formatted):
        allowed_list = self.get_ids_and_names(schedule_list_original)
        schedule_list = self.remove_unnecessary_keys_from_workout_schedule(schedule_list_original)
        schedule_summary = self.list_of_dicts_to_string(schedule_list)
        edit_prompt = self.edit_system_prompt_constructor(schedule_summary, schedule_formatted, allowed_list)
        return edit_prompt

    # Retrieves the fields from the Pydantic model output.
    def edit_model_to_dict(self, goal_edit):
        goal_edit_dump = goal_edit.model_dump()
        parsed_edit = {
            self.schedule_id_key: goal_edit_dump.pop("id", None)
        }

        # Alter the variables in the state to match those retrieved from the LLM.
        for key, value in goal_edit_dump.items():
            parsed_edit[key] = value
        
        print("Parsed Edit:")
        for key, value in parsed_edit.items():
            print(key, value)
        print("")

        return parsed_edit

    # Items extracted from the edit request.
    def goal_edits_parser(self, goal_edits=None):
        # Return an empty dictionary of edits if no edits were made.
        if not goal_edits:
            return {}
    
        goal_edits_dict={}
        
        # Convert goal edits to a dictionary format
        for goal_edit in goal_edits:
            goal_edits_dict[goal_edit.id] = self.edit_model_to_dict(goal_edit)

        return goal_edits_dict

    # Retrieve entry for the edit.
    def compare_edits(self, original_schedule, altered_schedule):
        edits_to_be_applyed = {}
        for original_schedule_item in original_schedule:
            original_schedule_item_id = original_schedule_item[self.schedule_id_key]

            # Skip the entry if the schedule item isn't present.
            if original_schedule_item_id not in altered_schedule.keys():
                continue

            altered_schedule_item = altered_schedule[original_schedule_item_id]

            common_keys = set(original_schedule_item.keys()) & set(altered_schedule_item.keys())

            # Include the item if it has been indicated to be removed.
            if altered_schedule_item.get("remove", False):
                edits_to_be_applyed[original_schedule_item_id] = altered_schedule_item

            # Only include the item if any value has been changed from the original.
            elif any(original_schedule_item[key] != altered_schedule_item[key] for key in common_keys):
                edits_to_be_applyed[original_schedule_item_id] = altered_schedule_item
        return edits_to_be_applyed

    # Items extracted from the edit request.
    def goal_edit_request_parser(self, goal_class, edits_to_be_applyed):
        return {
            "is_edited": True if edits_to_be_applyed else False,
            "edits": edits_to_be_applyed,
            # "should_regenerate": goal_class.regenerate,
            "other_requests": goal_class.other_requests
        }

    # Request permission from user to execute the parent initialization.
    def ask_for_edits(self, state: TState):
        LogEditorAgent.agent_steps(f"\t---------Ask user if edits should be made to the schedule---------")
        if not request_schedule_edits:
            LogEditorAgent.agent_steps(f"\t---------Agent settings do not request edits.---------")
            return {
                "is_edited": False,
                "edits": {},
                # "should_regenerate": False,
                "other_requests": None
            }
        # Get a copy of the current schedule and remove the items not useful for the AI.
        formatted_schedule_list = state["schedule_printed"]

        result = interrupt({
            "task": f"Are there any edits you would like to make to the schedule?\n\n{formatted_schedule_list}"
        })
        user_input = result["user_input"]
        LogEditorAgent.verbose(f"Extract the Edits from the following message: {user_input}")

        # Retrieve the schedule and format it for the prompt.
        schedule_list = state["agent_output"]
        edit_prompt = self.edit_prompt_creator(copy.deepcopy(schedule_list), state["schedule_printed"])

        # Retrieve the new input for the parent item.
        goal_class = new_input_request(user_input, edit_prompt, self.edit_goal)

        new_schedule = goal_class.schedule
        if new_schedule: 
            # Convert to dictionary form.
            goal_edits_dict = self.goal_edits_parser(new_schedule)

            # Refine and remove entries that weren't edited.
            edits_to_be_applyed = self.compare_edits(state["agent_output"], goal_edits_dict)
        else: 
            edits_to_be_applyed = {}

        return self.goal_edit_request_parser(goal_class, edits_to_be_applyed)

    # Specific code for extracting information from the edited schedule into the new one.
    def apply_edit_to_schedule_item(self, schedule_item, schedule_edit):
        pass

    # Perform the edits.
    def perform_edits(self, state: TState):
        LogEditorAgent.agent_steps(f"\t---------Performing the Requested Edits for the Schedule---------")

        # Retrieve the schedule and format it for the prompt.
        schedule_list = copy.deepcopy(state["agent_output"])
        schedule_edits = state["edits"]

        # Apply the edits to the schedule.
        for schedule_item in schedule_list:
            schedule_item_id = schedule_item[self.schedule_id_key]

            # Skip the entry if the schedule item isn't present.
            if schedule_item_id not in schedule_edits.keys():
                continue

            schedule_edit = schedule_edits[schedule_item_id]

            self.apply_edit_to_schedule_item(schedule_item, schedule_edit)
        
        return {"edited_schedule": schedule_list}

    def gather_schedule_violations(self, state):
        pass

    # Check if the user's edits produce a valid schedule.
    def check_if_schedule_is_valid(self, state: TState):
        LogEditorAgent.agent_steps(f"\t---------Check if Schedule is valid.---------")
        violations = self.gather_schedule_violations(state)

        # Determine if the schedule is valid.
        if violations:
            is_valid = False
            LogEditorAgent.agent_steps(f"\t---------No violations have been found.---------")
        else:
            is_valid = True
            LogEditorAgent.agent_steps(f"\t---------The following violations have been found:---------")
            for violation in violations:
                LogEditorAgent.agent_steps(f"\t{violation}")

        return {
            "violations": violations, 
            "is_valid": is_valid
        }

    # Format the structured schedule.
    def format_proposed_edited_list(self, state: TState):
        LogEditorAgent.agent_steps(f"\t---------Format Proposed Edited Workout Schedule---------")
        return self._get_formatted_proposed_list(state, "edited_schedule", "edited_schedule_printed")

    # Request permission from user to apply the requested edits.
    def ask_to_move_forward(self, state: TState):
        LogEditorAgent.agent_steps(f"\t---------Ask user if the new schedule should be applied---------")

        # Get a copy of the current schedule and remove the items not useful for the AI.
        formatted_schedule_list = state["edited_schedule_printed"]

        is_schedule_invalid = not(state["is_valid"])

        # Determine the task given to the user.
        if is_schedule_invalid and confirm_invalid_schedule:
            violations = list_to_str(state["violations"], newline=True)
            
            user_task = f"WARNING: THE FOLLOWING SCHEDULE DOES NOT FOLLOW RECOMMENDED GUIDELINES!!!\n\nViolations include:\n{violations}\n\nAre you sure you would like for the following schedule to be allowed?\n{formatted_schedule_list}"
        elif confirm_valid_schedule:
            user_task = f"Would you like to move forward with the following schedule?\n\n{formatted_schedule_list}"
        else:
            return {"allow_schedule": True}

        result = interrupt({
            "task": user_task
        })

        return {"allow_schedule": does_user_allow_schedule(result["user_input"], is_schedule_invalid)}

    # Finalize the proposed edits.
    def finalize_edits(self, state: TState):
        LogEditorAgent.agent_steps(f"\t---------Replacing Old Schedule with Edited Schedule---------")
        return {
            "schedule_printed": state["edited_schedule_printed"], 
            "agent_output": state["edited_schedule"]
        }

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogEditorAgent.agent_introductions(f"=========Ending Editor SubAgent=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class: type[TState] = AgentState):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("format_proposed_list", self.format_proposed_list)
        workflow.add_node("ask_for_edits", self.ask_for_edits)
        workflow.add_node("perform_edits", self.perform_edits)
        workflow.add_node("format_proposed_edited_list", self.format_proposed_edited_list)
        workflow.add_node("check_if_schedule_is_valid", self.check_if_schedule_is_valid)
        workflow.add_node("ask_to_move_forward", self.ask_to_move_forward)
        workflow.add_node("finalize_edits", self.finalize_edits)
        workflow.add_node("end_node", self.end_node)

        # Create a formatted list for the user to review.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "format_proposed_list")
        workflow.add_edge("format_proposed_list", "ask_for_edits")

        # Whether any edits have been applied.
        workflow.add_conditional_edges(
            "ask_for_edits",
            confirm_edits,
            {
                "is_edited": "perform_edits",                           # The agent should apply the desired edits to the schedule.
                "not_edited": "end_node"                                # The agent should end if no edits were found.
            }
        )
        workflow.add_edge("perform_edits", "format_proposed_edited_list")
        workflow.add_edge("format_proposed_edited_list", "check_if_schedule_is_valid")
        workflow.add_edge("check_if_schedule_is_valid", "ask_to_move_forward")

        # Whether the user wants to move forward with the new schedule.
        workflow.add_conditional_edges(
            "ask_to_move_forward",
            confirm_interest,
            {
                "allow_schedule": "finalize_edits",                      # The agent should finalize the edits.
                "do_not_allow_schedule": "ask_for_edits"                 # The agent should go back to the edit request.
            }
        )

        workflow.add_edge("finalize_edits", "ask_for_edits")

        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = BaseSubAgent()
    return agent.create_main_agent_graph()