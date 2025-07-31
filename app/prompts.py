from app.core.goal_prompt_generator import retrieve_system_prompt

from .user_weekdays_availability import availability_request
from .user_macrocycles import macrocycle_request
from .user_mesocycles import mesocycle_request
from .user_microcycles import microcycle_request
from .user_workout_days import phase_component_request
from .user_workout_exercises import workout_schedule_request
from .user_workout_completion import workout_complete_request

goal_extraction_request = {
    "description": f"""1. {availability_request["description"]}
2. {macrocycle_request["description"]}
3. {mesocycle_request["description"]}
4. {microcycle_request["description"]}
5. {phase_component_request["description"]}
6. {workout_schedule_request["description"]}
7. {workout_complete_request["description"]}""",
    "ex_output": f"""{availability_request["ex_output"]}
{macrocycle_request["ex_output"]}
{mesocycle_request["ex_output"]}
{microcycle_request["ex_output"]}
{phase_component_request["ex_output"]}
{workout_schedule_request["ex_output"]}
{workout_complete_request["ex_output"]}"""
}

goal_extraction_system_prompt = retrieve_system_prompt(goal_extraction_request)