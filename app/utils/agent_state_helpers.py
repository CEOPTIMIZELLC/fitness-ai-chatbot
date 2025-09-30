from logging_config import LogGeneral

from app.utils.global_variables import sub_agent_names

# Retrieves the last element appended to the path.
def retrieve_current_agent_focus(state, desired_element="focus"):
    current_path_items = state["agent_path"][-1]
    return current_path_items[desired_element]

def sub_agent_focused_items(sub_agent_focus):
    return {
        "entry": f"user_{sub_agent_focus}", 
        "id": f"{sub_agent_focus}_id", 
        "is_requested": f"{sub_agent_focus}_is_requested", 
        "is_alter": f"{sub_agent_focus}_is_alter", 
        "alter_detail": f"{sub_agent_focus}_alter_detail", 
        "is_read": f"{sub_agent_focus}_is_read", 
        "read_detail": f"{sub_agent_focus}_read_detail", 
        "is_create": f"{sub_agent_focus}_is_create", 
        "create_detail": f"{sub_agent_focus}_create_detail", 
        "is_delete": f"{sub_agent_focus}_is_delete", 
        "delete_detail": f"{sub_agent_focus}_delete_detail", 
        "read_plural": f"{sub_agent_focus}_read_plural", 
        "read_current": f"{sub_agent_focus}_read_current", 
        "detail": f"{sub_agent_focus}_detail", 
        "formatted": f"{sub_agent_focus}_formatted",
        "perform_with_parent_id": f"{sub_agent_focus}_perform_with_parent_id",
    }

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
    update_bool(state, old_state, updated_state, f"{section}_is_alter")
    update_bool(state, old_state, updated_state, f"{section}_is_read")
    update_val(state, old_state, updated_state, f"{section}_detail")
    return state

def agent_state_update(old_state, updated_state, ignore_section=None):
    state = {}
    for sub_agent_name in sub_agent_names:
        update_state_schedule_section(state, old_state, updated_state, sub_agent_name, ignore_section)
    return state

def log_extracted_goals(result):
    LogGeneral.other_request_updates(f"Goals extracted.")
    for sub_agent_name in sub_agent_names:
        if result.get(f"{sub_agent_name}_is_requested"):
            LogGeneral.other_request_updates(f"{sub_agent_name}: {result[f"{sub_agent_name}_detail"]}")
    LogGeneral.other_request_updates("")
    return None

def goal_classifier_parser(focus_names, goal_class):
    goal_class_dump = goal_class.model_dump()
    parsed_goal = {
        "other_requests": goal_class_dump.pop("other_requests", None)
    }

    # Alter the variables in the state to match those retrieved from the LLM.
    for key, value in goal_class_dump.items():
        if value is not None:
            parsed_goal[focus_names[key]] = value

    return parsed_goal