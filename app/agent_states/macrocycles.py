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
    macrocycle_alter_detail: str

    macrocycle_is_create: bool
    macrocycle_create_detail: str

    macrocycle_is_read: bool
    macrocycle_read_plural: str
    macrocycle_read_current: str
    macrocycle_read_detail: str

    macrocycle_is_delete: bool
    macrocycle_delete_detail: str

    macrocycle_read_plural: bool
    macrocycle_read_current: bool
    macrocycle_detail: str

    macrocycle_formatted: str
    macrocycle_perform_with_parent_id: int

    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int