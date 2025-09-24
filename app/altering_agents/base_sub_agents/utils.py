from logging_config import LogAlteringAgent
from flask import current_app
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Retrieves the last element appended to the path.
def retrieve_current_agent_focus(state, desired_element="focus"):
    current_path_items = state["agent_path"][-1]
    return current_path_items[desired_element]

def sub_agent_focused_items(sub_agent_focus):
    return {
        "entry": f"user_{sub_agent_focus}", 
        "id": f"{sub_agent_focus}_id", 
        "is_requested": f"{sub_agent_focus}_is_requested", 
        "is_altered": f"{sub_agent_focus}_is_altered", 
        "is_read": f"{sub_agent_focus}_is_read", 
        "read_plural": f"{sub_agent_focus}_read_plural", 
        "read_current": f"{sub_agent_focus}_read_current", 
        "detail": f"{sub_agent_focus}_detail", 
        "formatted": f"{sub_agent_focus}_formatted",
        "perform_with_parent_id": f"{sub_agent_focus}_perform_with_parent_id",
    }

# Request permission from user to execute the parent initialization.
def new_input_request(user_input, item_system_prompt, item_goal):
    LogAlteringAgent.system_message(item_system_prompt)
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
    LogAlteringAgent.parsed_goal(f"Parsed Goal Fields: ")
    for key, value in goal_dict.items():
        LogAlteringAgent.parsed_goal(f"{key}: {value}")
    LogAlteringAgent.parsed_goal(f"")

    return goal_class

# Extract the individual item
def _user_input_sub_extraction(state, sub_agent_name, sub_agent_pydantic):
    state[f"{sub_agent_name}_is_requested"] = sub_agent_pydantic["is_requested"]
    state[f"{sub_agent_name}_is_altered"] = True
    state[f"{sub_agent_name}_is_read"] = True
    state[f"{sub_agent_name}_detail"] = sub_agent_pydantic["detail"]
    return state

# Update the original value to be the new message if one is present.
def update_val(final_state, old_state, updated_state, key):
    final_state[key] = updated_state.get(key, old_state.get(key))
    return final_state

# Update the boolean to be True if either the current or previous request was true.
def update_bool(final_state, old_state, updated_state, key):
    final_state[key] = old_state.get(key, False) or updated_state.get(key, False)
    return final_state

# Update a schedule section 
def update_state_schedule_section(state, old_state, updated_state, section, ignore_section):
    if section == ignore_section:
        return state
    update_bool(state, old_state, updated_state, f"{section}_is_requested")
    update_bool(state, old_state, updated_state, f"{section}_is_altered")
    update_bool(state, old_state, updated_state, f"{section}_is_read")
    update_val(state, old_state, updated_state, f"{section}_detail")
    return state