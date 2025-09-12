from .utils import retrieve_system_prompt

microcycle_request = {
    "description": """**Microcycle** - Weekly routine structure (e.g., changing number of training days, spacing of workouts).""", 
    "ex_output": """- `microcycle`: is_requested = true, detail = "User wants to train 5 days per week." """}

microcycle_system_prompt = retrieve_system_prompt(microcycle_request)