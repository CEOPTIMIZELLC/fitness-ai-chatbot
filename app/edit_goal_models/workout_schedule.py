from pydantic import BaseModel, Field
from typing import Optional, List

class Exercise(BaseModel):
    """Performance metrics of the exercise."""
    # You could match on pc_id, name, or both
    id: int = Field(
        ..., description="The id of exercise in question."
    )
    exercise_name: str = Field(
        ..., description="The name of the exercise in question."
    )
    # If the user wants to remove this exercise:
    remove: bool = Field(
        False, description="True ONLY if the exercise has been indicated to be removed."
    )
    # New values (None means “no change”)
    reps: int = Field(
        ..., description="The reps for the exercise in question."
    )
    sets: int = Field(
        ..., description="The sets for the exercise in question."
    )
    rest: int = Field(
        ..., description="The rest for the exercise in question. Can be 0."
    )
    weight: float = Field(
        ..., description="The weight for the exercise in question."
    )


# Model to extract information on whether the user wants to edit something.
class WorkoutScheduleEditGoal(BaseModel):
    """Goal extraction from user input regarding editing the current workout schedule."""
    schedule: List[Exercise] = Field(
        [], description="Details about what the values of the schedule elements."
    )
    regenerate: bool = Field(
        False, description="Whether the user has explicitly stated they would like for an entirely new schedule to be generated."
    )
    other_requests: Optional[str] = Field(
        None, description="All information not immedately relevant to the edits to the schedule should be made here. Does not impact the 'is_schedule_edited' field."
    )