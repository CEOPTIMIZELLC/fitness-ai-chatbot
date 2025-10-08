from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the exercise routine from user input.
class RoutineImpactGoals(BaseModel):
    """Hierarchical goal extraction from user input regarding exercise routine."""
    availability: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the requests to read, alter, create, and delete availability for the user."
    )
    macrocycle: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the requests to read, alter, create, and delete macrocycles for the user."
    )
    mesocycle: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the requests to read, alter, create, and delete mesocycles for the user."
    )
    microcycle: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the requests to read, alter, create, and delete microcycles for the user."
    )
    phase_component: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the requests to read, alter, create, and delete phase components for the user."
    )
    workout_schedule: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the requests to read, alter, create, and delete workout schedules for the user."
    )
    workout_completion: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the requests indicating that a previous workout has been completed for the user."
    )
    equipment: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the requests to read, alter, create, and delete equipment belonging the user."
    )