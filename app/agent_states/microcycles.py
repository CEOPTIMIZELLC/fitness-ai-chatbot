from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str

    microcycle_is_alter: bool
    microcycle_alter_detail: str

    microcycle_is_create: bool
    microcycle_create_detail: str

    microcycle_is_read: bool
    microcycle_read_plural: str
    microcycle_read_current: str
    microcycle_read_detail: str

    microcycle_is_delete: bool
    microcycle_delete_detail: str

    user_mesocycle: dict
    mesocycle_id: int
    microcycle_count: int
    microcycle_duration: any
    start_date: any