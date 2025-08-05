from pydantic import BaseModel, Field
from typing import Optional

# Model to extract information on whether the user wants to edit something.
class EditGoal(BaseModel):
    """Goal extraction from user input regarding editing the current schedule."""
    is_requested: bool = Field(
        ..., description="True if the user indicates a desire to change something in the currently presented schedule."
    )
    detail: Optional[str] = Field(
        None, description="Details about what updates should be made. ONLY include detail if changes are proposed."
    )
    other_requests: Optional[str] = Field(
        None, description="All information not immedately relevant to the edits to the schedule should be made here."
    )