from app.core.goal_prompt_generator import retrieve_system_prompt

workout_complete_request = {
    "description": """**Workout Complete** — Specifically indicates whether the user has completed their current workout. This should only be true if the user has SPECIFICALLY mentioned that they have completed their workout.""", 
    "ex_output": """- `workout_completion`: is_requested = false, detail = null """}

workout_complete_system_prompt = retrieve_system_prompt(workout_complete_request)