from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    temp_mesocycle_is_alter: bool
    temp_mesocycle_alter_detail: str
    temp_mesocycle_is_create: bool
    temp_mesocycle_create_detail: str
    temp_mesocycle_is_read: bool
    temp_mesocycle_read_detail: str
    temp_mesocycle_is_delete: bool
    temp_mesocycle_delete_detail: str

    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int
    start_date: any
    macrocycle_allowed_weeks: int
    possible_phases: list
    agent_output: list
    should_regenerate: bool
    schedule_printed: str