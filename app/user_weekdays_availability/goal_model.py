from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Availability from user input.
class AvailabilityGoal(BaseModel):
    """Goal extraction from user input regarding user weekday availability."""
    is_requested: bool = Field(
        ..., description="True if the user indicates a change in their weekday or time availability."
    )
    detail: Optional[str] = Field(
        None, description="Details about updated availability such as new time windows or days."
    )
