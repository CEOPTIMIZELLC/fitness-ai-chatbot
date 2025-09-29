from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    temp_phase_component_is_alter: bool
    temp_phase_component_alter_detail: str
    temp_phase_component_is_create: bool
    temp_phase_component_create_detail: str
    temp_phase_component_is_read: bool
    temp_phase_component_read_detail: str
    temp_phase_component_is_delete: bool
    temp_phase_component_delete_detail: str

    user_microcycle: dict
    microcycle_id: int
    phase_id: int
    duration: any

    microcycle_weekdays: list
    user_availability: list
    weekday_availability: list
    number_of_available_weekdays: int
    total_availability: int

    start_date: any
    agent_output: list
    schedule_printed: str