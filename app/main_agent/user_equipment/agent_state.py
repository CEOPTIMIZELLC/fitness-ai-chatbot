from app.main_agent.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str

    item_id: int
    equipment_id: int
    equipment_measurement: int
    new_equipment_id: int
    new_equipment_measurement: int