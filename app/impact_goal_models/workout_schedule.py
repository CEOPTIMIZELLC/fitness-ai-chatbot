from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Workout Schedule from user input.
class WorkoutScheduleGoal(BaseModel):
    """Goal extraction from user input regarding user workout schedules."""
    is_requested: bool = Field(
        ..., description="True if the user wants to directly modify the exercises or structure of specific workouts."
    )
    detail: Optional[str] = Field(
        None, description="Workout-specific updates like 'replace squats with lunges on leg day' or 'add more core work on Tuesday'."
    )