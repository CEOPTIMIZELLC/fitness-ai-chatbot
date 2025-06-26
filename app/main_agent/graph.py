from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from flask import current_app

from .prompts import goal_extraction_system_prompt

from app.main_agent_steps import (
    MacrocycleActions, 
    MesocycleActions, 
    MicrocycleActions, 
    MicrocycleSchedulerActions, 
    WorkoutActions, 
    WeekdayAvailabilitySchedulerActions)

class AgentState(TypedDict):
    user_input: str
    check: bool
    attempts: int

    availability_impacted: bool
    availability_message: str
    macrocycle_impacted: bool
    macrocycle_message: str
    mesocycle_impacted: bool
    mesocycle_message: str
    microcycle_impacted: bool
    microcycle_message: str
    phase_component_impacted: bool
    phase_component_message: str
    workout_schedule_impacted: bool
    workout_schedule_message: str

from .impact_goal_models import RoutineImpactGoals


def user_input_information_extraction(state: AgentState):
    user_input = state["user_input"]

    print(f"Extract the goals from the following message: {user_input}")
    human = f"Extract the goals from the following message: {user_input}"
    # human = f"New_goal: {user_input}"
    check_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", goal_extraction_system_prompt),
            ("human", human),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(RoutineImpactGoals)
    goal_classifier = check_prompt | structured_llm
    goal_class = goal_classifier.invoke({})

    state["availability_impacted"] = goal_class.availability.is_requested
    state["availability_message"] = goal_class.availability.detail
    state["macrocycle_impacted"] = goal_class.macrocycle.is_requested
    state["macrocycle_message"] = goal_class.macrocycle.detail
    state["mesocycle_impacted"] = goal_class.mesocycle.is_requested
    state["mesocycle_message"] = goal_class.mesocycle.detail
    state["microcycle_impacted"] = goal_class.microcycle.is_requested
    state["microcycle_message"] = goal_class.microcycle.detail
    state["phase_component_impacted"] = goal_class.phase_component.is_requested
    state["phase_component_message"] = goal_class.phase_component.detail
    state["workout_schedule_impacted"] = goal_class.workout_schedule.is_requested
    state["workout_schedule_message"] = goal_class.workout_schedule.detail

    print(f"Goals extracted.")
    if state["availability_impacted"]:
        print(f"availability: {state["availability_message"]}")
    if state["macrocycle_impacted"]:
        print(f"macrocycle: {state["macrocycle_message"]}")
    if state["mesocycle_impacted"]:
        print(f"mesocycle: {state["mesocycle_message"]}")
    if state["microcycle_impacted"]:
        print(f"microcycle: {state["microcycle_message"]}")
    if state["phase_component_impacted"]:
        print(f"phase_component: {state["phase_component_message"]}")
    if state["workout_schedule_impacted"]:
        print(f"workout_schedule: {state["workout_schedule_message"]}")
    print("")

    return state

def check_availability_node(state: AgentState):
    print(f"Checking User Availability")
    state["check"] = state["availability_impacted"]
    return state

def availability_node(state: AgentState):
    print(f"Changing User Availability")
    availability_message = state["availability_message"]
    print(f"{availability_message}")
    new_availability = WeekdayAvailabilitySchedulerActions.scheduler(availability_message)
    return state

def check_macrocycle_node(state: AgentState):
    print(f"Checking User Macrocycle")
    state["check"] = state["macrocycle_impacted"]
    return state

def macrocycle_node(state: AgentState):
    print(f"Changing User Macrocycle")
    macrocycle_message = state["macrocycle_message"]
    print(f"{macrocycle_message}")
    macrocycles = MacrocycleActions.scheduler(macrocycle_message)
    return state

def check_mesocycle_node(state: AgentState):
    print(f"Checking User Mesocycle")
    state["check"] = state["mesocycle_impacted"]
    return state

def mesocycle_node(state: AgentState):
    print(f"Changing User Mesocycle")
    mesocycle_message = state["mesocycle_message"]
    print(f"{mesocycle_message}")
    result = MesocycleActions.scheduler()
    result["formatted_schedule"] = MesocycleActions.get_formatted_list()
    return state

def check_microcycle_node(state: AgentState):
    print(f"Checking User Microcycle")
    state["check"] = state["microcycle_impacted"]
    return state

def microcycle_node(state: AgentState):
    print(f"Changing User Microcycle")
    microcycle_message = state["microcycle_message"]
    print(f"{microcycle_message}")
    result = MicrocycleActions.scheduler()
    return state

def check_phase_component_node(state: AgentState):
    print(f"Checking User Phase Component")
    state["check"] = state["phase_component_impacted"]
    return state

def phase_component_node(state: AgentState):
    print(f"Changing User Phase Component")
    phase_component_message = state["phase_component_message"]
    print(f"{phase_component_message}")
    result = MicrocycleSchedulerActions.scheduler()
    result["formatted_schedule"] = MicrocycleSchedulerActions.get_formatted_list()
    return state

def check_workout_schedule_node(state: AgentState):
    print(f"Checking User Workout Schedule")
    state["check"] = state["workout_schedule_impacted"]
    return state

def workout_schedule_node(state: AgentState):
    print(f"Changing User Workout Schedule")
    workout_schedule_message = state["workout_schedule_message"]
    print(f"{workout_schedule_message}")
    result = WorkoutActions.scheduler()
    result["formatted_schedule"] = WorkoutActions.get_formatted_list()
    return state

def print_schedule_node(state: AgentState):
    print(f"Printing Schedule")
    print(f"Goals extracted.")
    if state["availability_impacted"]:
        print(f"availability: {state["availability_message"]}")
    if state["macrocycle_impacted"]:
        print(f"macrocycle: {state["macrocycle_message"]}")
    if state["mesocycle_impacted"]:
        print(f"mesocycle: {state["mesocycle_message"]}")
    if state["microcycle_impacted"]:
        print(f"microcycle: {state["microcycle_message"]}")
    if state["phase_component_impacted"]:
        print(f"phase_component: {state["phase_component_message"]}")
    if state["workout_schedule_impacted"]:
        print(f"workout_schedule: {state["workout_schedule_message"]}")
    print("")

    return state

def goal_router(state: AgentState):
    return state["check"]

def construct_goal_edge(workflow, previous_node, node_if_true, node_if_false):
    current_checking_node = f"check_{node_if_true}"

    # Advance a successful node to the next check
    workflow.add_edge(previous_node, current_checking_node)
    workflow.add_conditional_edges(
        current_checking_node,
        goal_router,
        {
            True: node_if_true,
            False: node_if_false
        }
    )
    return None

def create_main_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("user_input_extraction", user_input_information_extraction)

    workflow.add_node("check_availability", check_availability_node)
    workflow.add_node("availability", availability_node)

    workflow.add_node("check_macrocycle", check_macrocycle_node)
    workflow.add_node("macrocycle", macrocycle_node)

    workflow.add_node("check_mesocycle", check_mesocycle_node)
    workflow.add_node("mesocycle", mesocycle_node)

    workflow.add_node("check_microcycle", check_microcycle_node)
    workflow.add_node("microcycle", microcycle_node)

    workflow.add_node("check_phase_component", check_phase_component_node)
    workflow.add_node("phase_component", phase_component_node)

    workflow.add_node("check_workout_schedule", check_workout_schedule_node)
    workflow.add_node("workout_schedule", workout_schedule_node)

    workflow.add_node("print_schedule", print_schedule_node)

    # User Input to Availability
    construct_goal_edge(workflow, "user_input_extraction", "availability", "check_macrocycle")

    # Availability to Macrocycles
    construct_goal_edge(workflow, "availability", "macrocycle", "check_mesocycle")

    # Macrocycles to Mesocycles
    construct_goal_edge(workflow, "macrocycle", "mesocycle", "check_microcycle")

    # Mesocycles to Microcycles
    construct_goal_edge(workflow, "mesocycle", "microcycle", "check_phase_component")

    # Microcycles to Phase Components
    construct_goal_edge(workflow, "microcycle", "phase_component", "check_workout_schedule")

    # Phase Components to Workout Exercises
    construct_goal_edge(workflow, "phase_component", "workout_schedule", "print_schedule")

    # Workout Exercises to End
    workflow.add_edge("workout_schedule", "print_schedule")
    workflow.add_edge("print_schedule", END)

    workflow.set_entry_point("user_input_extraction")

    return workflow.compile()
