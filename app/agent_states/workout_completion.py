from app.agent_states.main_agent_state import MainAgentState

class AgentState(MainAgentState):
    focus_name: str
    parent_name: str
    user_workout_day: dict
    workout_day_id: int
    user_exercises: list
    old_user_exercises: list
    agent_output: list
    schedule_printed: str