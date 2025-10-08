from pydantic import BaseModel, Field

from app.utils.user_input import new_input_request

class MoveForwardWithSchedule(BaseModel):
    allow_schedule: bool = Field(
        False, description="True ONLY if the user has indicated that they want to move forward with their schedule."
    )


confirm_valid_schedule_edit_prompt = """
You are an expert on conversational analysis. 

A user has been presented with a schedule they have requested and is going to indicate whether or not they would like to continue with this schedule. 

You are to extract the structured information from the user's input regarding whether or not they would like to move forward with this schedule.
"""


confirm_invalid_schedule_edit_prompt = """
You are an expert on conversational analysis. 

A user has been presented with the fact that a schedule they have requested is not recommended and is going to indicate whether or not they would like to continue with this schedule. 

You are to extract the structured information from the user's input regarding whether or not they would like to move forward with this schedule.
"""

# Request permission from user to allow edits that aren't advised.
def does_user_allow_schedule(user_input, is_schedule_invalid=False):
    # Retrieve whether the user wants to move forward with the not reccommended.
    if is_schedule_invalid:
        goal_class = new_input_request(user_input, confirm_invalid_schedule_edit_prompt, MoveForwardWithSchedule)

    else:
        goal_class = new_input_request(user_input, confirm_valid_schedule_edit_prompt, MoveForwardWithSchedule)

    return goal_class.allow_schedule