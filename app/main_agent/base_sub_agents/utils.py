from logging_config import LogMainSubAgent
from flask import current_app
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.impact_goal_models import RoutineImpactGoals
from app.goal_prompts import goal_extraction_system_prompt

def sub_agent_focused_items(sub_agent_focus):
    return {
        "entry": f"user_{sub_agent_focus}", 
        "id": f"{sub_agent_focus}_id", 
        "impact": f"{sub_agent_focus}_impacted", 
        "is_altered": f"{sub_agent_focus}_is_altered", 
        "read_plural": f"{sub_agent_focus}_read_plural", 
        "read_current": f"{sub_agent_focus}_read_current", 
        "message": f"{sub_agent_focus}_message", 
        "formatted": f"{sub_agent_focus}_formatted",
        "perform_with_parent_id": f"{sub_agent_focus}_perform_with_parent_id",
    }

# Request permission from user to execute the parent initialization.
def new_input_request(user_input, item_system_prompt, item_goal):
    human = f"Extract the goals from the following message: {user_input}"
    check_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", item_system_prompt),
            ("human", human),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(item_goal)
    goal_classifier = check_prompt | structured_llm
    goal_class = goal_classifier.invoke({})

    # Convert the Pydantic model to a dictionary
    goal_dict = goal_class.model_dump()

    # Iterate and print names and values
    LogMainSubAgent.parsed_goal(f"Parsed Goal Fields: ")
    for key, value in goal_dict.items():
        LogMainSubAgent.parsed_goal(f"{key}: {value}")
    LogMainSubAgent.parsed_goal(f"")

    return goal_class

def user_input_information_extraction(user_input):
    state={}

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

    state["attempts"] = 1
    state["availability_impacted"] = goal_class.availability.is_requested
    state["availability_is_altered"] = True
    state["availability_message"] = goal_class.availability.detail
    state["macrocycle_impacted"] = goal_class.macrocycle.is_requested
    state["macrocycle_is_altered"] = True
    state["macrocycle_message"] = goal_class.macrocycle.detail
    state["macrocycle_alter_old"] = goal_class.macrocycle.alter_old
    state["mesocycle_impacted"] = goal_class.mesocycle.is_requested
    state["mesocycle_is_altered"] = True
    state["mesocycle_message"] = goal_class.mesocycle.detail
    state["microcycle_impacted"] = goal_class.microcycle.is_requested
    state["microcycle_is_altered"] = True
    state["microcycle_message"] = goal_class.microcycle.detail
    state["phase_component_impacted"] = goal_class.phase_component.is_requested
    state["phase_component_is_altered"] = True
    state["phase_component_message"] = goal_class.phase_component.detail
    state["workout_schedule_impacted"] = goal_class.workout_schedule.is_requested
    state["workout_schedule_is_altered"] = True
    state["workout_schedule_message"] = goal_class.workout_schedule.detail
    state["workout_completion_impacted"] = goal_class.workout_completion.is_requested
    state["workout_completion_is_altered"] = True
    state["workout_completion_message"] = goal_class.workout_completion.detail

    return state


# Update the original value to be the new message if one is present.
def update_val(final_state, old_state, updated_state, key):
    final_state[key] = updated_state.get(key, old_state.get(key))
    return final_state

# Update the boolean to be True if either the current or previous request was true.
def update_bool(final_state, old_state, updated_state, key):
    final_state[key] = old_state.get(key, False) or updated_state.get(key, False)
    return final_state

def agent_state_update(old_state, updated_state):
    LogMainSubAgent.agent_steps(f"\n=========Update other requests=========")
    state = {}
    update_bool(state, old_state, updated_state, "availability_impacted")
    update_bool(state, old_state, updated_state, "availability_is_altered")
    update_val(state, old_state, updated_state, "availability_message")

    update_bool(state, old_state, updated_state, "macrocycle_impacted")
    update_bool(state, old_state, updated_state, "macrocycle_is_altered")
    update_val(state, old_state, updated_state, "macrocycle_message")
    update_bool(state, old_state, updated_state, "macrocycle_alter_old")

    update_bool(state, old_state, updated_state, "mesocycle_impacted")
    update_bool(state, old_state, updated_state, "mesocycle_is_altered")
    update_val(state, old_state, updated_state, "mesocycle_message")

    update_bool(state, old_state, updated_state, "microcycle_impacted")
    update_bool(state, old_state, updated_state, "microcycle_is_altered")
    update_val(state, old_state, updated_state, "microcycle_message")

    update_bool(state, old_state, updated_state, "phase_component_impacted")
    update_bool(state, old_state, updated_state, "phase_component_is_altered")
    update_val(state, old_state, updated_state, "phase_component_message")

    update_bool(state, old_state, updated_state, "workout_schedule_impacted")
    update_bool(state, old_state, updated_state, "workout_schedule_is_altered")
    update_val(state, old_state, updated_state, "workout_schedule_message")

    update_bool(state, old_state, updated_state, "workout_completion_impacted")
    update_bool(state, old_state, updated_state, "workout_completion_is_altered")
    update_val(state, old_state, updated_state, "workout_completion_message")

    return state
