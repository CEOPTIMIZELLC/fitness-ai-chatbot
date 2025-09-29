from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    phase_component_is_alter: bool
    phase_component_alter_detail: str
    phase_component_is_create: bool
    phase_component_create_detail: str
    phase_component_is_read: bool
    phase_component_read_detail: str
    phase_component_read_plural: str
    phase_component_read_current: str
    phase_component_is_delete: bool
    phase_component_delete_detail: str

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