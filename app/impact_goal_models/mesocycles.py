from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Mesocycle from user input.
class MesocycleGoalPart(BaseModel):
    """Goal extraction from user input regarding user mesocycles."""
    is_requested: bool = Field(
        ..., description="True if the user indicates desired changes to the structure or focus of mesocycles, such as shifting phases or changing durations."
    )
    detail: Optional[str] = Field(
        None, description="Specific requests such as 'add a strength phase after hypertrophy' or 'reduce deload to 1 week'."
    )

# Model to extract information along with additional requests.
class MesocycleGoal(MesocycleGoalPart):
    other_requests: Optional[str] = Field(
        None, description="All information and requests not immedately relevant to the mesocycle requests."
    )