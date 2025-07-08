from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from flask import current_app
from flask_login import current_user


from .prompts import goal_extraction_system_prompt

from .user_macrocycles import MacrocycleActions, create_goal_agent
from .user_mesocycles import MesocycleActions, create_mesocycle_agent
from .user_microcycles import MicrocycleActions, create_microcycle_agent
from .user_workout_days import MicrocycleSchedulerActions, create_microcycle_scheduler_agent
from .user_workout_exercises import WorkoutActions
from .user_weekdays_availability import WeekdayAvailabilitySchedulerActions

from .impact_goal_models import RoutineImpactGoals
from .main_agent_state import MainAgentState as AgentState

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

    state["user_id"] = current_user.id
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

def availability_node(state: AgentState):
    print(f"\n=========Changing User Availability=========")
    if state["availability_impacted"]:
        availability_message = state["availability_message"]
        new_availability = WeekdayAvailabilitySchedulerActions.scheduler(availability_message)
    else:
        availability_message = None
    print(f"{availability_message}")
    return {"availability_formatted": availability_message}

def workout_schedule_node(state: AgentState):
    print(f"\n=========Changing User Workout Schedule=========")
    if state["workout_schedule_impacted"]:
        workout_schedule_message = state["workout_schedule_message"]
        result = WorkoutActions.scheduler()
        result["formatted_schedule"] = WorkoutActions.get_formatted_list()
    else:
        workout_schedule_message = None
    print(f"{workout_schedule_message}")
    return {"workout_schedule_formatted": workout_schedule_message}

def print_schedule_node(state: AgentState):
    print(f"\n=========Printing Schedule=========")
    print(f"Goals extracted.")
    if state["availability_impacted"]:
        print(f"availability: {state["availability_formatted"]}")
    if state["macrocycle_impacted"]:
        print(f"macrocycle: {state["macrocycle_formatted"]}")
    if state["mesocycle_impacted"]:
        print(f"mesocycle: {state["mesocycle_formatted"]}")
    if state["microcycle_impacted"]:
        print(f"microcycle: {state["microcycle_formatted"]}")
    if state["phase_component_impacted"]:
        print(f"phase_component: {state["phase_component_formatted"]}")
    if state["workout_schedule_impacted"]:
        print(f"workout_schedule: {state["workout_schedule_formatted"]}")
    print("")

    return state

# Create main agent.
def create_main_agent_graph():
    goal_agent = create_goal_agent()
    mesocycle_agent = create_mesocycle_agent()
    microcycle_agent = create_microcycle_agent()
    microcycle_scheduler_agent = create_microcycle_scheduler_agent()

    workflow = StateGraph(AgentState)

    workflow.add_node("user_input_extraction", user_input_information_extraction)

    workflow.add_node("availability", availability_node)
    workflow.add_node("macrocycle", goal_agent)
    workflow.add_node("mesocycle", mesocycle_agent)
    workflow.add_node("microcycle", microcycle_agent)
    workflow.add_node("phase_component", microcycle_scheduler_agent)
    workflow.add_node("workout_schedule", workout_schedule_node)
    workflow.add_node("print_schedule", print_schedule_node)

    # User Input to Availability and Macrocycles
    workflow.add_edge("user_input_extraction", "availability")
    workflow.add_edge("user_input_extraction", "macrocycle")

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
    workflow.add_edge("print_schedule", END)

    workflow.set_entry_point("user_input_extraction")

    return workflow.compile()
