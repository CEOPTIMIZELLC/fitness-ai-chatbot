from .utils import retrieve_system_prompt

phase_component_request = {
    "description": """**Phase Components** - Specific requests about which types of workouts should be included in a single microcycle (e.g., more endurance, less strength).""", 
    "ex_output": """- `phase_component`: is_requested = false, detail = null """}

phase_component_system_prompt = retrieve_system_prompt(phase_component_request)