from .utils import retrieve_system_prompt

mesocycle_request = {
    "description": """**Mesocycle** - Level where the focus/phase for a month within a Macrocycle is determined. Modifications to the training blocks or phases (e.g., shifting from strength to hypertrophy, changing phase durations).""", 
    "ex_output": """- `mesocycle`: is_requested = true, detail = "User wants to shift focus to hypertrophy for this mesocycle." """}

mesocycle_system_prompt = retrieve_system_prompt(mesocycle_request)