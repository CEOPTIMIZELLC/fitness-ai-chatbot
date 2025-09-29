from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str

    temp_equipment_is_alter: bool
    temp_equipment_alter_detail: str
    temp_equipment_is_create: bool
    temp_equipment_create_detail: str
    temp_equipment_is_read: bool
    temp_equipment_read_detail: str
    temp_equipment_is_delete: bool
    temp_equipment_delete_detail: str

    item_id: int
    equipment_id: int
    equipment_name: str
    equipment_measurement: int
    new_equipment_id: int
    new_equipment_name: str
    new_equipment_measurement: int
    available_equipment: list