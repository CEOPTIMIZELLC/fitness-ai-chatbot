from app.core.goal_prompt_generator import retrieve_system_prompt

workout_schedule_request = {
    "description": """**Workout Schedule** — Specific exercise-level requests within a workout (e.g., changing exercises, sets, reps, or focus).""", 
    "ex_output": """- `workout_schedule`: is_requested = true, detail = "Add core work to the upper body workout." """}

workout_schedule_system_prompt = retrieve_system_prompt(workout_schedule_request)