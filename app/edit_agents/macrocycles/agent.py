from config import request_schedule_edits
from logging_config import LogEditorAgent

from datetime import date, timedelta
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app import db
from app.models import Goal_Library
from app.schedule_printers import MacrocycleSchedulePrinter
from app.edit_agents.base.base import ScheduleFormatterMethods
from app.edit_agents.base.utils import new_input_request

from .edit_goal_model import MacrocycleScheduleEditGoal
from .edit_prompt import MacrocycleEditPrompt

keys_to_remove = [
    "name", 
    "goal_id", 
    "goal", 
]

class AgentState(TypedDict):
    is_edited: bool
    edits: any
    other_requests: str
    agent_output: dict
    schedule_printed: str

    macrocycle_detail: str
    goal_id: int
    start_date: any
    end_date: any
    available_goals: list

# Confirm that the desired section should be edited.
def confirm_edits(state):
    LogEditorAgent.agent_steps(f"\t---------Confirm that the Schedule is Edited---------")
    if state["is_edited"]:
        LogEditorAgent.agent_steps(f"\t---------Is Edited---------")
        return "is_edited"
    return "not_edited"

class SubAgent(ScheduleFormatterMethods, MacrocycleEditPrompt):
    edit_goal = MacrocycleScheduleEditGoal
    list_printer_class = MacrocycleSchedulePrinter()
    schedule_id_key = "id"
    schedule_name_key = "goal_name"
    keys_to_remove = keys_to_remove

    # Node to declare that the sub agent has ended.
    def start_node(self, state):
        LogEditorAgent.agent_introductions(f"=========Starting Editor SubAgent=========\n")
        return {}

    # Format the structured schedule.
    def construct_agent_output(self, state: AgentState):
        LogEditorAgent.agent_steps(f"\t---------Construct Agent Output From Macrocycle Information---------")
        current_date = date.today()

        items = Goal_Library.query.all()
        
        # Create the list of available goals for the LLM to choose from.
        goals_list = [
            {
                "id": item.id, 
                "goal_name": item.name
            } for item in items
        ]

        # Get the start and end dates for the macrocycle.
        start_date = state.get("start_date", current_date)
        end_date = state.get("start_date", current_date + timedelta(weeks=26))

        total_duration = end_date - start_date
        duration = f"{total_duration.days // 7} weeks {total_duration.days % 7} days"

        return {
            "agent_output": {
                "id": state["goal_id"],
                "goal_name": db.session.get(Goal_Library, state["goal_id"]).name, 
                "start_date": start_date, 
                "end_date": end_date, 
                "duration": duration
            }, 
            "available_goals": goals_list
        }

    # Format the structured schedule.
    def format_proposed_list(self, state: AgentState):
        LogEditorAgent.agent_steps(f"\t---------Format Proposed Workout Schedule---------")
        schedule_list = state["agent_output"]

        formatted_schedule = self.list_printer_class.run_printer([schedule_list])
        LogEditorAgent.formatted_schedule(formatted_schedule)

        return {
            "agent_output": schedule_list, 
            "schedule_printed": formatted_schedule
        }

    # Create prompt to request schedule edits.
    def edit_prompt_creator(self, current_goal, available_goals):
        allowed_list = self.get_ids_and_names(available_goals)
        schedule_summary = self.dict_to_string(current_goal)
        edit_prompt = self.edit_system_prompt_constructor(schedule_summary, allowed_list)
        return edit_prompt

    # Retrieve entry for the edit.
    def compare_edits(self, original_schedule, altered_schedule):
        edits_to_be_applyed = {}

        # Only include the item if any value has been changed from the original.
        for key in altered_schedule:
            if original_schedule[key] != altered_schedule[key]:
                edits_to_be_applyed[key] = altered_schedule[key]
        return edits_to_be_applyed

    # Request permission from user to execute the parent initialization.
    def ask_for_edits(self, state: AgentState):
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
        current_goal = state["agent_output"]
        available_goals = state["available_goals"]
        edit_prompt = self.edit_prompt_creator(current_goal, available_goals)

        # Retrieve the new input for the parent item.
        goal_class = new_input_request(user_input, edit_prompt, self.edit_goal)

        goal_id = goal_class.id
        new_goal = next((d for d in available_goals if d.get("id") == goal_id), None)

        # Convert to dictionary form.
        goal_edits_dict = {
            self.schedule_id_key: goal_id, 
            "goal_name": new_goal["goal_name"], 
            "start_date": goal_class.start_date, 
            "end_date": goal_class.end_date, 
        }

        # Refine and remove entries that weren't edited.
        edits_to_be_applyed = self.compare_edits(state["agent_output"], goal_edits_dict)

        return {
            "is_edited": True if edits_to_be_applyed else False,
            "edits": edits_to_be_applyed,
            # "should_regenerate": goal_class.regenerate,
            "other_requests": goal_class.other_requests
        }

    # Perform the edits.
    def perform_edits(self, state: AgentState):
        LogEditorAgent.agent_steps(f"\t---------Performing the Requested Edits for the Schedule---------")

        # Retrieve the schedule and format it for the prompt.
        schedule = state["agent_output"]
        schedule_edits = state["edits"]

        # Apply the edits to the schedule.
        for key, value in schedule_edits.items():
            schedule[key] = value

        # Get the start and end dates for the macrocycle.
        start_date = schedule["start_date"]
        end_date = schedule["end_date"]

        total_duration = end_date - start_date
        duration = f"{total_duration.days // 7} weeks {total_duration.days % 7} days"

        return {
            "agent_output": schedule, 
            "goal_id": schedule["id"], 
            "start_date": start_date, 
            "end_date": end_date, 
            "duration": duration, 
        }

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        LogEditorAgent.agent_introductions(f"=========Ending Editor SubAgent=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, state_class = AgentState):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("construct_agent_output", self.construct_agent_output)
        workflow.add_node("format_proposed_list", self.format_proposed_list)
        workflow.add_node("ask_for_edits", self.ask_for_edits)
        workflow.add_node("perform_edits", self.perform_edits)
        workflow.add_node("end_node", self.end_node)

        # Create a formatted list for the user to review.
        workflow.add_edge(START, "start_node")
        workflow.add_edge("start_node", "construct_agent_output")
        workflow.add_edge("construct_agent_output", "format_proposed_list")
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
        workflow.add_edge("perform_edits", "format_proposed_list")

        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph()