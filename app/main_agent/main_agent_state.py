
from typing_extensions import TypedDict
class MainAgentState(TypedDict):
    user_id: int

    user_input: str
    check: bool
    attempts: int

    is_edited: bool
    edits: any
    other_requests: str
    macrocycle_other_requests: str
    availability_other_requests: str

    availability_impacted: bool
    availability_is_altered: bool
    availability_read_plural: bool
    availability_read_current: bool
    availability_message: str
    availability_formatted: str
    availability_perform_with_parent_id: int

    macrocycle_impacted: bool
    macrocycle_is_altered: bool
    macrocycle_read_plural: bool
    macrocycle_read_current: bool
    macrocycle_message: str
    macrocycle_formatted: str
    macrocycle_perform_with_parent_id: int
    macrocycle_alter_old: bool

    mesocycle_impacted: bool
    mesocycle_is_altered: bool
    mesocycle_read_plural: bool
    mesocycle_read_current: bool
    mesocycle_message: str
    mesocycle_formatted: str
    mesocycle_perform_with_parent_id: int

    microcycle_impacted: bool
    microcycle_is_altered: bool
    microcycle_read_plural: bool
    microcycle_read_current: bool
    microcycle_message: str
    microcycle_formatted: str
    microcycle_perform_with_parent_id: int

    phase_component_impacted: bool
    phase_component_is_altered: bool
    phase_component_read_plural: bool
    phase_component_read_current: bool
    phase_component_message: str
    phase_component_formatted: str
    phase_component_perform_with_parent_id: int

    workout_schedule_impacted: bool
    workout_schedule_is_altered: bool
    workout_schedule_read_plural: bool
    workout_schedule_read_current: bool
    workout_schedule_message: str
    workout_schedule_formatted: str
    workout_schedule_perform_with_parent_id: int

    workout_completion_impacted: bool
    workout_completion_is_altered: bool
    workout_completion_read_plural: bool
    workout_completion_read_current: bool
    workout_completion_message: str
    workout_completion_formatted: str
    workout_completion_perform_with_parent_id: int
