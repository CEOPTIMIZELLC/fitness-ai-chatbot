from .utils import retrieve_system_prompt

workout_completion_request = {
    "description": """**Workout Completion** - Specifically indicates whether the user has completed their current workout. This should only be true if the user has SPECIFICALLY mentioned that they have completed their workout.""", 
    "ex_output": """- `workout_completion`: is_requested = false, detail = null """}

workout_completion_system_prompt = retrieve_system_prompt(workout_completion_request)