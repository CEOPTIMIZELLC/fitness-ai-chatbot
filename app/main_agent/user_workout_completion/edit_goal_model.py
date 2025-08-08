from pydantic import BaseModel, Field
from typing import Optional, List

class ExerciseEdit(BaseModel):
    """Instructions of what items to change or remove from an exercise."""
    # You could match on pc_id, name, or both
    id: int = Field(
        ..., description="The id of exercise in question. This should not be changed from the original exercise at all."
    )
    exercise_name: str = Field(
        ..., description="The name of the exercise in question."
    )
    # If the user wants to remove this exercise:
    remove: Optional[bool] = Field(
        False, description="True ONLY if the exercise has been indicated to be removed."
    )
    # New values (None means “no change”)
    reps: Optional[int] = Field(
        None, description="The reps specified by the user for the exercise. A value of None means that no change has been indicated."
    )
    sets: Optional[int] = Field(
        None, description="The sets specified by the user for the exercise. A value of None means that no change has been indicated."
    )
    rest: Optional[int] = Field(
        None, description="The rest specified by the user for the exercise. A value of None means that no change has been indicated."
    )
    weight: Optional[float] = Field(
        None, description="The weight specified by the user for the exercise. A value of None means that no change has been indicated."
    )


# Model to extract information on whether the user wants to edit something.
class EditGoal(BaseModel):
    """Goal extraction from user input regarding editing the current workout schedule."""
    edits: Optional[List[ExerciseEdit]] = Field(
        [], description="Details about what updates should be made."
    )
    other_requests: Optional[str] = Field(
        None, description="All information not immedately relevant to the edits to the schedule should be made here. Does not impact the 'is_schedule_edited' field."
    )