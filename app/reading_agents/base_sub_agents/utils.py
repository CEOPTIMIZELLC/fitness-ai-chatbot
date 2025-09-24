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
