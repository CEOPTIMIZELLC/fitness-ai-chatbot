from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Equipment from user input.
class EquipmentGoalPart(BaseModel):
    """Goal extraction from user input regarding user equipment."""
    is_requested: bool = Field(
        ..., description="True if the user indicates desired changes to the structure or focus of equipment, such as shifting phases or changing durations."
    )
    detail: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the equipment specifically."
    )

# Model to extract information along with additional requests.
class EquipmentGoal(EquipmentGoalPart):
    other_requests: Optional[str] = Field(
        None, description="All information and requests not immedately relevant to the equipment requests."
    )