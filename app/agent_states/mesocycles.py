from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    mesocycle_is_alter: bool
    mesocycle_alter_detail: str
    mesocycle_is_create: bool
    mesocycle_create_detail: str
    mesocycle_is_read: bool
    mesocycle_read_detail: str
    mesocycle_read_plural: str
    mesocycle_read_current: str
    mesocycle_is_delete: bool
    mesocycle_delete_detail: str

    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int
    start_date: any
    macrocycle_allowed_weeks: int
    possible_phases: list
    agent_output: list
    should_regenerate: bool
    schedule_printed: str