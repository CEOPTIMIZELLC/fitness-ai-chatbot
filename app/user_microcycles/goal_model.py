from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Microcycle from user input.
class MicrocycleGoal(BaseModel):
    """Goal extraction from user input regarding user microcycles."""
    is_requested: bool = Field(
        ..., description="True if the user wants to adjust their microcycle (weekly) structure, e.g., number of training days or workout frequency."
    )
    detail: Optional[str] = Field(
        None, description="Requested changes such as 'train 4 days per week' or 'add a rest day midweek'."
    )
