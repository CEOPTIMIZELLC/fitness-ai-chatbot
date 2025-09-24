from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    user_phase_component: dict
    phase_component_id: int
    loading_system_id: int

    user_availability: int
    start_date: any
    agent_output: list
    should_regenerate: bool
    schedule_printed: str