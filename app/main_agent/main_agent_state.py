
from typing_extensions import TypedDict
class MainAgentState(TypedDict):
    user_id: int
    agent_path: list

    user_input: str
    check: bool
    attempts: int

    is_edited: bool
    edits: any
    other_requests: str
    macrocycle_other_requests: str
    availability_other_requests: str

    equipment_is_requested: bool
    equipment_is_altered: bool
    equipment_read_plural: bool
    equipment_read_current: bool
    equipment_detail: str
    equipment_formatted: str
    equipment_perform_with_parent_id: int
    equipment_alter_old: bool

    availability_is_requested: bool
    availability_is_altered: bool
    availability_read_plural: bool
    availability_read_current: bool
    availability_detail: str
    availability_formatted: str
    availability_perform_with_parent_id: int

    macrocycle_is_requested: bool
    macrocycle_is_altered: bool
    macrocycle_read_plural: bool
    macrocycle_read_current: bool
    macrocycle_detail: str
    macrocycle_formatted: str
    macrocycle_perform_with_parent_id: int
    macrocycle_alter_old: bool

    mesocycle_is_requested: bool
    mesocycle_is_altered: bool
    mesocycle_read_plural: bool
    mesocycle_read_current: bool
    mesocycle_detail: str
    mesocycle_formatted: str
    mesocycle_perform_with_parent_id: int

    microcycle_is_requested: bool
    microcycle_is_altered: bool
    microcycle_read_plural: bool
    microcycle_read_current: bool
    microcycle_detail: str
    microcycle_formatted: str
    microcycle_perform_with_parent_id: int

    phase_component_is_requested: bool
    phase_component_is_altered: bool
    phase_component_read_plural: bool
    phase_component_read_current: bool
    phase_component_detail: str
    phase_component_formatted: str
    phase_component_perform_with_parent_id: int

    workout_schedule_is_requested: bool
    workout_schedule_is_altered: bool
    workout_schedule_read_plural: bool
    workout_schedule_read_current: bool
    workout_schedule_detail: str
    workout_schedule_formatted: str
    workout_schedule_perform_with_parent_id: int

    workout_completion_is_requested: bool
    workout_completion_is_altered: bool
    workout_completion_read_plural: bool
    workout_completion_read_current: bool
    workout_completion_detail: str
    workout_completion_formatted: str
    workout_completion_perform_with_parent_id: int
