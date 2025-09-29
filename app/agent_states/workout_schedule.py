from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    workout_schedule_is_alter: bool
    workout_schedule_alter_detail: str
    workout_schedule_is_create: bool
    workout_schedule_create_detail: str
    workout_schedule_is_read: bool
    workout_schedule_read_detail: str
    workout_schedule_read_plural: str
    workout_schedule_read_current: str
    workout_schedule_is_delete: bool
    workout_schedule_delete_detail: str

    user_phase_component: dict
    phase_component_id: int
    loading_system_id: int

    user_availability: int
    start_date: any
    agent_output: list
    should_regenerate: bool
    schedule_printed: str