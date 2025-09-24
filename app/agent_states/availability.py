from typing_extensions import TypedDict

class AgentState(TypedDict):
    user_id: int
    focus_name: str
    agent_path: list

    user_input: str
    attempts: int
    other_requests: str

    availability_is_requested: bool
    availability_is_altered: bool
    availability_is_read: bool
    availability_read_plural: bool
    availability_read_current: bool
    availability_detail: str
    availability_formatted: str

    agent_output: list