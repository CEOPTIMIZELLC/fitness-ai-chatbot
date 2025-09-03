from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class Mesocycle(BaseModel):
    """Performance metrics of the mesocycle."""
    # You could match on pc_id, name, or both
    id: int = Field(
        ..., description="The id of mesocycle in question."
    )
    mesocycle_name: str = Field(
        ..., description="The name of the mesocycle in question."
    )
    # If the user wants to remove this mesocycle:
    remove: bool = Field(
        False, description="True ONLY if the mesocycle has been indicated to be removed."
    )
    start_date: date = Field(
        ..., description="The date for the start of the mesocycle in question."
    )
    end_date: date = Field(
        ..., description="The date for the end of the mesocycle in question."
    )


# Model to extract information on whether the user wants to edit something.
class MesocycleScheduleEditGoal(BaseModel):
    """Goal extraction from user input regarding editing the current mesocycle schedule."""
    schedule: List[Mesocycle] = Field(
        [], description="Details about what the values of the schedule elements."
    )
    regenerate: bool = Field(
        False, description="Whether the user has explicitly stated they would like for an entirely new schedule to be generated."
    )
    other_requests: Optional[str] = Field(
        None, description="All information not immedately relevant to the edits to the schedule should be made here. Does not impact the 'is_schedule_edited' field."
    )