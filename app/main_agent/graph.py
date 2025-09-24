from config import loop_main_agent
from logging_config import LogMainAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from flask import current_app

from app.goal_prompts import goal_extraction_system_prompt

from .base_sub_agents.utils import user_input_information_extraction

from .user_equipment import create_equipment_agent
from .user_macrocycles import MacrocycleAgentNode
from .user_mesocycles import create_mesocycle_agent
from .user_microcycles import create_microcycle_agent
from .user_workout_days import create_microcycle_scheduler_agent
from .user_workout_exercises import create_workout_agent
from .user_workout_completion import create_workout_completion_agent
from .user_weekdays_availability import WeekdayAvailabilityAgentNode

from app.impact_goal_models import RoutineImpactGoals
from app.agent_states.main_agent_state import MainAgentState as AgentState

sub_agent_names = [
    "equipment", 
    "workout_completion", 
    "availability", 
    "macrocycle", 
    "mesocycle", 
    "microcycle", 
    "phase_component", 
    "workout_schedule", 
]

# Resets the value of an item in the state to None if it exists.
def reset_schedule_item(state, state_item):
    state[state_item] = None
    return state

# Resets the value of a boolean in the state to False if it exists.
def reset_schedule_bool(state, state_item):
    state[state_item] = False
    return state

# Resets the values related to a schedule section in the state to None.
def reset_schedule_section(state, schedule_name):
    reset_schedule_bool(state, f"{schedule_name}_is_requested")
    reset_schedule_bool(state, f"{schedule_name}_is_altered")
    reset_schedule_bool(state, f"{schedule_name}_is_read")
    reset_schedule_bool(state, f"{schedule_name}_read_plural")
    reset_schedule_bool(state, f"{schedule_name}_read_current")
    reset_schedule_item(state, f"{schedule_name}_detail")
    reset_schedule_item(state, f"{schedule_name}_formatted")
    reset_schedule_item(state, f"{schedule_name}_perform_with_parent_id")
    return state

# Confirm that the desired section should be impacted.
def confirm_input(state):
    LogMainAgent.agent_introductions(f"\n=========Beginning Main Agent=========")
    LogMainAgent.agent_steps(f"---------Confirm that an Input Exists---------")
    if not state["user_input"]:
        LogMainAgent.agent_steps(f"---------No Input---------")
        return "no_input"
    return "included_input"

# Determine if the agent should be looping or end after one iteration.
def is_agent_a_loop(state: AgentState):
    LogMainAgent.agent_steps(f"---------Check if Main Agent should loop---------")
    if loop_main_agent:
        return "yes_loop"
    return "no_loop"

class MainAgent(WeekdayAvailabilityAgentNode, MacrocycleAgentNode):
    def entry_node(self, state: AgentState):
        LogMainAgent.agent_introductions(f"\n=========Beginning Main Agent=========")
        # Reset to None for testing
        for sub_agent_name in sub_agent_names:
            state = reset_schedule_section(state, sub_agent_name)
        state["agent_path"] = []
        return state

    # Request User Input.
    def ask_for_user_request(self, state: AgentState):
        LogMainAgent.agent_steps(f"---------Ask user for a new request---------")
        result = interrupt({
            "task": f"Hello there! How can I help you today?"
        })
        user_input = result["user_input"]
        LogMainAgent.verbose(f"New request: {user_input}")
        
        state["user_input"] = user_input
        return state

    def user_input_information_extraction(self, state: AgentState):
        LogMainAgent.agent_steps(f"\n=========Extract Input=========")
        user_input = state["user_input"]

        LogMainAgent.verbose(f"Extract the goals from the following message: {user_input}")
        state_updates = user_input_information_extraction(user_input)
        for key, value in state_updates.items():
            state[key] = value

        LogMainAgent.input_info(f"Goals extracted.")
        for sub_agent_name in sub_agent_names:
            if state[f"{sub_agent_name}_is_requested"]:
                LogMainAgent.input_info(f"{sub_agent_name}: {state[f"{sub_agent_name}_detail"]}")
        LogMainAgent.input_info("")

        return state

    def print_schedule_node(self, state: AgentState):
        LogMainAgent.agent_steps(f"\n=========Printing Schedule=========")
        LogMainAgent.formatted_schedule(f"Schedule Generatted.")
        for sub_agent_name in sub_agent_names:
            if (f"{sub_agent_name}_formatted" in state) and (state[f"{sub_agent_name}_is_requested"]):
                LogMainAgent.formatted_schedule(f"{sub_agent_name}: \n{state[f"{sub_agent_name}_formatted"]}")
        LogMainAgent.formatted_schedule("")

        return state

    # Node to declare that the sub agent has ended.
    def end_node(self, state: AgentState):
        LogMainAgent.agent_introductions(f"=========Ending Main Agent=========\n")
        # Reset to None for testing
        for sub_agent_name in sub_agent_names:
            state = reset_schedule_section(state, sub_agent_name)
        state["agent_path"] = []
        return state

    # Create main agent.
    def create_main_agent_graph(self, checkpointer=None):
        mesocycle_agent = create_mesocycle_agent()
        microcycle_agent = create_microcycle_agent()
        microcycle_scheduler_agent = create_microcycle_scheduler_agent()
        workout_agent = create_workout_agent()
        workout_completion_agent = create_workout_completion_agent()
        equipment_agent = create_equipment_agent()

        workflow = StateGraph(AgentState)

        workflow.add_node("entry_node", self.entry_node)
        workflow.add_node("ask_for_user_request", self.ask_for_user_request)
        workflow.add_node("user_input_extraction", self.user_input_information_extraction)
        workflow.add_node("availability", self.availability_node)
        workflow.add_node("macrocycle", self.macrocycle_node)
        workflow.add_node("mesocycle", mesocycle_agent)
        workflow.add_node("microcycle", microcycle_agent)
        workflow.add_node("phase_component", microcycle_scheduler_agent)
        workflow.add_node("workout_schedule", workout_agent)
        workflow.add_node("workout_completion", workout_completion_agent)
        workflow.add_node("equipment", equipment_agent)
        workflow.add_node("print_schedule", self.print_schedule_node)
        workflow.add_node("end_node", self.end_node)

        workflow.add_edge("entry_node", "ask_for_user_request")

        # Check whether a user input exists.
        workflow.add_conditional_edges(
            "ask_for_user_request",
            confirm_input,
            {
                "no_input": "end_node",                                     # End the agent if no input is given.
                "included_input": "user_input_extraction"                   # Parse the user input if one is given.
            }
        )

        # User Input to Workout Completion
        workflow.add_edge("user_input_extraction", "workout_completion")

        # Workout Completion to Equipment
        workflow.add_edge("workout_completion", "equipment")

        # Workout Completion to Availability and Macrocycles
        workflow.add_edge("equipment", "availability")
        workflow.add_edge("equipment", "macrocycle")

        # Availability and Macrocycles to Mesocycles
        workflow.add_edge("macrocycle", "mesocycle")
        workflow.add_edge("availability", "mesocycle")

        # Mesocycles to Microcycles
        workflow.add_edge("mesocycle", "microcycle")

        # Microcycles to Phase Components
        workflow.add_edge("microcycle", "phase_component")

        # Phase Components to Workout Exercises
        workflow.add_edge("phase_component", "workout_schedule")

        # Workout Exercises to End
        workflow.add_edge("workout_schedule", "print_schedule")

        # Check whether the agent should loop.
        workflow.add_conditional_edges(
            "print_schedule",
            is_agent_a_loop,
            {
                "no_loop": "end_node",                                      # End the agent if it shouldn't loop.
                "yes_loop": "ask_for_user_request"                          # Restart agent if it should loop.
            }
        )

        workflow.set_entry_point("entry_node")
        workflow.set_finish_point("end_node")

        return workflow.compile(checkpointer=checkpointer)

# Create main agent.
def create_main_agent_graph(checkpointer):
    agent = MainAgent()
    return agent.create_main_agent_graph(checkpointer)