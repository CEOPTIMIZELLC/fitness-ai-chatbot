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
    alter_old: Optional[bool] = Field(
        default=False, description="Whether the new piece of equipment is altering an old piece of equipment or if a new piece of equipment is requested. Only true if explicitly mentioned. Only applicable if equipment is requested."
    )
    delete_old: Optional[bool] = Field(
        default=False, description="Whether the desired outcome is to delete an old piece of equipment. Only true if explicitly mentioned. Only applicable if equipment is requested."
    )

# Model to extract information along with additional requests.
class EquipmentGoal(EquipmentGoalPart):
    other_requests: Optional[str] = Field(
        None, description="All information and requests not immedately relevant to the equipment requests."
    )