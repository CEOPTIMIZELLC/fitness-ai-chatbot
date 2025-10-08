from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class Availability(BaseModel):
    """Performance metrics of the weekday availability."""
    # You could match on pc_id, name, or both
    id: int = Field(
        ..., description="The id of weekday in question."
    )
    weekday_name: str = Field(
        ..., description="The name of the weekday in question."
    )
    availability: int = Field(
        ..., description="The availability in seconds for the weekday in question."
    )

# Model to extract information on whether the user wants to edit something.
class AvailabilityScheduleEditGoal(BaseModel):
    """Goal extraction from user input regarding editing the current weekday availability schedule."""
    schedule: List[Availability] = Field(
        [], description="Details about what the values of the schedule elements."
    )
    regenerate: bool = Field(
        False, description="Whether the user has explicitly stated they would like for an entirely new schedule to be generated."
    )
    other_requests: Optional[str] = Field(
        None, description="All information not immedately relevant to the edits to the schedule should be made here. Does not impact the 'is_schedule_edited' field."
    )