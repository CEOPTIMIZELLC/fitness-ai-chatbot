from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the WorkoutCompletion from user input.
class WorkoutCompletionGoal(BaseModel):
    """Goal extraction from user input regarding user workout completion."""
    is_requested: bool = Field(
        ..., description="True if the has completed their workout."
    )
    detail: Optional[str] = Field(
        None, description="Details like if the user only completed part of their workout."
    )
