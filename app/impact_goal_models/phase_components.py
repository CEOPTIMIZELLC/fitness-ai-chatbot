from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Phase Component from user input.
class PhaseComponentGoal(BaseModel):
    """Goal extraction from user input regarding user phase components."""
    is_requested: bool = Field(
        ..., description="True if the user wants to modify the distribution of phase components (e.g., hypertrophy, strength, endurance) within a microcycle."
    )
    detail: Optional[str] = Field(
        None, description="Details like 'replace strength with hypertrophy on Thursday' or 'more focus on power training in this microcycle'."
    )