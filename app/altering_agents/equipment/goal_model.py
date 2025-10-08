from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Equipment from user input.
class Equipment(BaseModel):
    """Goal extraction from user input regarding user equipment."""
    unique_id: Optional[int] = Field(
        None, description="The unique_id that corresponds to a user's individual piece of equipment."
    )
    equipment_id: Optional[int] = Field(
        None, description="The equipment_id that corresponds to the type of equipment the user wants to add."
    )
    equipment_measurement: Optional[int] = Field(
        None, description="The measurement that the user has specified for their equipment."
    )

# Model to extract information along with additional requests.
class EquipmentGoal(Equipment):
    other_requests: Optional[str] = Field(
        None, description="All information and requests not immedately relevant to the equipment requests."
    )

# Model to extract goal information for the Equipment from user input.
class EquipmentNew(BaseModel):
    """Goal extraction from user input regarding the new equipment."""
    equipment_id: Optional[int] = Field(
        None, description="The equipment_id that corresponds to the type of equipment the user wants to add."
    )
    equipment_measurement: Optional[int] = Field(
        None, description="The new measurement that the user wants for the old piece of equipment."
    )

# Model to extract information along with additional requests.
class EquipmentRequests(BaseModel):
    old_equipment_information: Optional[Equipment] = Field(
        None, description="All information and requests from the original message relating to the equipment that should be edited."
    )
    new_equipment_information: Optional[EquipmentNew] = Field(
        None, description="All information and requests from the original message relating to the changes that the user wants to make to their old equipment."
    )
    other_requests: Optional[str] = Field(
        None, description="All information and requests not immedately relevant to the equipment requests."
    )