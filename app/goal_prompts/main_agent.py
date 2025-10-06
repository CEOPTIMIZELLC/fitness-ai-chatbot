from .utils import retrieve_system_prompt

from .equipment import equipment_request
from .availability import availability_request
from .macrocycles import macrocycle_request
from .mesocycles import mesocycle_request
from .microcycles import microcycle_request
from .phase_components import phase_component_request
from .workout_schedule import workout_schedule_request
from .workout_completion import workout_completion_request

goal_extraction_request = {
    "description": f"""1. {equipment_request["description"]}
2. {availability_request["description"]}
3. {macrocycle_request["description"]}
4. {mesocycle_request["description"]}
5. {microcycle_request["description"]}
6. {phase_component_request["description"]}
7. {workout_schedule_request["description"]}
8. {workout_completion_request["description"]}""",
    "ex_output": f"""
{equipment_request["ex_output"]}
{availability_request["ex_output"]}
{macrocycle_request["ex_output"]}
{mesocycle_request["ex_output"]}
{microcycle_request["ex_output"]}
{phase_component_request["ex_output"]}
{workout_schedule_request["ex_output"]}
{workout_completion_request["ex_output"]}"""
}

goal_extraction_system_prompt = retrieve_system_prompt(goal_extraction_request)