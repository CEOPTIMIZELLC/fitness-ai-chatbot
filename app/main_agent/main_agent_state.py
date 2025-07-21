
from typing_extensions import TypedDict
class MainAgentState(TypedDict):
    user_id: int

    user_input: str
    check: bool
    attempts: int

    availability_impacted: bool
    availability_is_altered: bool
    availability_message: str
    availability_formatted: str

    macrocycle_impacted: bool
    macrocycle_is_altered: bool
    macrocycle_message: str
    macrocycle_formatted: str
    macrocycle_alter_old: bool

    mesocycle_impacted: bool
    mesocycle_is_altered: bool
    mesocycle_message: str
    mesocycle_formatted: str

    microcycle_impacted: bool
    microcycle_is_altered: bool
    microcycle_message: str
    microcycle_formatted: str

    phase_component_impacted: bool
    phase_component_is_altered: bool
    phase_component_message: str
    phase_component_formatted: str

    workout_schedule_impacted: bool
    workout_schedule_is_altered: bool
    workout_schedule_message: str
    workout_schedule_formatted: str

    workout_completion_impacted: bool
    workout_completion_is_altered: bool
    workout_completion_message: str
    workout_completion_formatted: str
