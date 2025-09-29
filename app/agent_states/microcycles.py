from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    temp_microcycle_is_alter: bool
    temp_microcycle_alter_detail: str
    temp_microcycle_is_create: bool
    temp_microcycle_create_detail: str
    temp_microcycle_is_read: bool
    temp_microcycle_read_detail: str
    temp_microcycle_is_delete: bool
    temp_microcycle_delete_detail: str

    user_mesocycle: dict
    mesocycle_id: int
    microcycle_count: int
    microcycle_duration: any
    start_date: any