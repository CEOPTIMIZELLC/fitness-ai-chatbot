from typing_extensions import TypedDict

class AgentState(TypedDict):
    user_id: int
    focus_name: str
    agent_path: list

    user_input: str
    attempts: int
    other_requests: str

    macrocycle_is_requested: bool
    macrocycle_is_alter: bool
    macrocycle_is_read: bool

    temp_macrocycle_is_alter: bool
    temp_macrocycle_alter_detail: str
    temp_macrocycle_is_create: bool
    temp_macrocycle_create_detail: str
    temp_macrocycle_is_read: bool
    temp_macrocycle_read_detail: str
    temp_macrocycle_is_delete: bool
    temp_macrocycle_delete_detail: str

    macrocycle_read_plural: bool
    macrocycle_read_current: bool
    macrocycle_detail: str
    macrocycle_formatted: str
    macrocycle_perform_with_parent_id: int
    macrocycle_alter_old: bool

    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int