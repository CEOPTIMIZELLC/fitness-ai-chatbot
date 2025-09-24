from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

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