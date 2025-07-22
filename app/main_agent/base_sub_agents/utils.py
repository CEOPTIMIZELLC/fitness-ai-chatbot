

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