from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Macrocycle from user input.
class MacrocycleGoalPart(BaseModel):
    """Goal extraction from user input regarding user macrocycles."""
    is_requested: bool = Field(
        ..., description="True if the user is indicating a change to their long-term training goals, e.g., muscle gain, fat loss, or sport-specific goals."
    )
    detail: Optional[str] = Field(
        None, description="Extracted long-term training goals such as 'gain strength in 12 weeks' or 'prepare for a marathon'."
    )

# Model to extract information along with additional requests.
class MacrocycleGoal(MacrocycleGoalPart):
    other_requests: Optional[str] = Field(
        None, description="All information and requests not immedately relevant to the macrocycle requests."
    )