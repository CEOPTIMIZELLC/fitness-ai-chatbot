
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
    equipment_detail: str
    equipment_formatted: str
    equipment_list_output: list
    equipment_perform_with_parent_id: int

    availability_is_requested: bool
    availability_detail: str
    availability_formatted: str
    availability_list_output: list
    availability_perform_with_parent_id: int

    macrocycle_is_requested: bool
    macrocycle_detail: str
    macrocycle_formatted: str
    macrocycle_list_output: list
    macrocycle_perform_with_parent_id: int

    mesocycle_is_requested: bool
    mesocycle_detail: str
    mesocycle_formatted: str
    mesocycle_list_output: list
    mesocycle_perform_with_parent_id: int

    microcycle_is_requested: bool
    microcycle_detail: str
    microcycle_formatted: str
    microcycle_list_output: list
    microcycle_perform_with_parent_id: int

    phase_component_is_requested: bool
    phase_component_detail: str
    phase_component_formatted: str
    phase_component_list_output: list
    phase_component_perform_with_parent_id: int

    workout_schedule_is_requested: bool
    workout_schedule_detail: str
    workout_schedule_formatted: str
    workout_schedule_list_output: list
    workout_schedule_perform_with_parent_id: int

    workout_completion_is_requested: bool
    workout_completion_detail: str
    workout_completion_formatted: str
    workout_completion_list_output: list
    workout_completion_perform_with_parent_id: int
