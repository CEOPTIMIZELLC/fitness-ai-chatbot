from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class Macrocycle(BaseModel):
    """Performance metrics of the macrocycle."""
    # You could match on pc_id, name, or both
    id: int = Field(
        ..., description="The id of macrocycle in question."
    )
    goal_name: str = Field(
        ..., description="The name of the macrocycle in question."
    )
    start_date: date = Field(
        ..., description="The date for the start of the macrocycle in question."
    )
    end_date: date = Field(
        ..., description="The date for the end of the macrocycle in question."
    )


# Model to extract information on whether the user wants to edit something.
class MacrocycleScheduleEditGoal(Macrocycle):
    """Goal extraction from user input regarding editing the current macrocycle schedule."""
    regenerate: bool = Field(
        False, description="Whether the user has explicitly stated they would like for an entirely new schedule to be generated."
    )
    other_requests: Optional[str] = Field(
        None, description="All information not immedately relevant to the edits to the schedule should be made here. Does not impact the 'is_schedule_edited' field."
    )