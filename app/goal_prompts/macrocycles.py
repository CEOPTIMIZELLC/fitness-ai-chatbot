from .utils import retrieve_system_prompt

macrocycle_request = {
    "description": """**Macrocycle** - Level where the over all goal/focus of the entire Macrocycle is determined. Updates to their long-term goals, such as focusing on muscle gain, fat loss, or sport performance over several months.""", 
    "ex_output": """- `macrocycle`: is_requested = false, detail = null """}

macrocycle_system_prompt = retrieve_system_prompt(macrocycle_request)