from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Availability from user input.
class AvailabilityGoalPart(BaseModel):
    """Goal extraction from user input regarding user weekday availability."""
    is_requested: bool = Field(
        ..., description="True if the user indicates a change in their weekday or time availability."
    )
    detail: Optional[str] = Field(
        None, description="Details about updated availability such as new time windows or days."
    )

# Model to extract information along with additional requests.
class AvailabilityGoal(AvailabilityGoalPart):
    other_requests: Optional[str] = Field(
        None, description="All information and requests not immedately relevant to the availability."
    )