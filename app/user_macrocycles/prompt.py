from app.core.goal_prompt_generator import retrieve_system_prompt

macrocycle_request = {
    "description": """**Macrocycle** — Updates to their long-term goals, such as focusing on muscle gain, fat loss, or sport performance over several months.""", 
    "ex_output": """- `macrocycle`: is_requested = false, detail = null """}

macrocycle_system_prompt = retrieve_system_prompt(macrocycle_request)