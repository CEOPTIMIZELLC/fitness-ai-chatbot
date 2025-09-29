from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str

    equipment_is_alter: bool
    equipment_alter_detail: str
    equipment_is_create: bool
    equipment_create_detail: str
    equipment_is_read: bool
    equipment_read_detail: str
    equipment_read_plural: str
    equipment_read_current: str
    equipment_is_delete: bool
    equipment_delete_detail: str

    item_id: int
    equipment_id: int
    equipment_name: str
    equipment_measurement: int
    new_equipment_id: int
    new_equipment_name: str
    new_equipment_measurement: int
    available_equipment: list