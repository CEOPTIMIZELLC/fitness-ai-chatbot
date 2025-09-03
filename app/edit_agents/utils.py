from logging_config import LogMainSubAgent

from pydantic import BaseModel, Field

from app.main_agent.base_sub_agents.utils import new_input_request

class MoveForwardWithSchedule(BaseModel):
    allow_schedule: bool = Field(
        False, description="True ONLY if the user has indicated that they want to move forward with their schedule."
    )

# Request permission from user to allow edits that aren't advised.
def does_user_allow_schedule(user_input):
    LogMainSubAgent.verbose(f"Extract the confirmation from the following message: {user_input}")

    edit_prompt = """
You are an expert on conversational analysis. 

A user has been presented with the fact that a schedule they have requested is not recommended and is going to indicate whether or not they would like to continue with this schedule. 

You are to extract the structured information from the user's input regarding whether or not they would like to move forward with this schedule.
"""

    # Retrieve whether the user wants to move forward with the not reccommended.
    goal_class = new_input_request(user_input, edit_prompt, MoveForwardWithSchedule)

    return goal_class.allow_schedule