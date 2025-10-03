from .utils import retrieve_system_prompt

equipment_request = {
    "description": """**Equipment** - Updates to the pieces of equipment that the user owns.""", 
    "ex_output": """- `equipment`: is_requested = false, detail = null """}

equipment_system_prompt = retrieve_system_prompt(equipment_request)