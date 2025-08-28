from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the WorkoutCompletion from user input.
class WorkoutCompletionGoalPart(BaseModel):
    """Goal extraction from user input regarding user workout completion."""
    is_requested: bool = Field(
        ..., description="True if the has completed their workout."
    )
    detail: Optional[str] = Field(
        None, description="Details like if the user only completed part of their workout."
    )

# Model to extract information along with additional requests.
class WorkoutCompletionGoal(WorkoutCompletionGoalPart):
    other_requests: Optional[str] = Field(
        None, description="All information and requests not immedately relevant to the workout completion requests."
    )
