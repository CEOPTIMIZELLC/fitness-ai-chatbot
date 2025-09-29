from typing_extensions import TypedDict

class AgentState(TypedDict):
    user_id: int
    focus_name: str
    agent_path: list

    user_input: str
    attempts: int
    other_requests: str

    availability_is_requested: bool

    availability_is_alter: bool
    availability_alter_detail: str
    availability_is_create: bool
    availability_create_detail: str
    availability_is_read: bool
    availability_read_detail: str
    availability_read_plural: str
    availability_read_current: str
    availability_is_delete: bool
    availability_delete_detail: str

    availability_read_plural: bool
    availability_read_current: bool
    availability_detail: str
    availability_formatted: str

    agent_output: list