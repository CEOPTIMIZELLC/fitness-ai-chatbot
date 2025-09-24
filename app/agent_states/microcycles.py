from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    user_mesocycle: dict
    mesocycle_id: int
    microcycle_count: int
    microcycle_duration: any
    start_date: any