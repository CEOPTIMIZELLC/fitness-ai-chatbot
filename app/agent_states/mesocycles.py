from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int
    start_date: any
    macrocycle_allowed_weeks: int
    possible_phases: list
    agent_output: list
    should_regenerate: bool
    schedule_printed: str