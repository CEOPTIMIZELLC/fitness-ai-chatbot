from pydantic import BaseModel, Field
from typing import Optional

# Model to extract goal information for the Availability from user input.
class AvailabilityGoal(BaseModel):
    """Goal extraction from user input regarding user weekday availability."""
    is_requested: bool = Field(
        ..., description="True if the user indicates a change in their weekday or time availability."
    )
    detail: Optional[str] = Field(
        None, description="Details about updated availability such as new time windows or days."
    )

# Model to extract goal information for the Macrocycle from user input.
class MacrocycleGoal(BaseModel):
    """Goal extraction from user input regarding user macrocycles."""
    is_requested: bool = Field(
        ..., description="True if the user is indicating a change to their long-term training goals, e.g., muscle gain, fat loss, or sport-specific goals."
    )
    detail: Optional[str] = Field(
        None, description="Extracted long-term training goals such as 'gain strength in 12 weeks' or 'prepare for a marathon'."
    )
    alter_old: Optional[bool] = Field(
        default=False, description="Whether the new macrocycle should alter the current goal instead of replacing it. Only true if explicitly mentioned. Only applicable if macrocycle is requested."
    )

# Model to extract goal information for the Mesocycle from user input.
class MesocycleGoal(BaseModel):
    """Goal extraction from user input regarding user mesocycles."""
    is_requested: bool = Field(
        ..., description="True if the user indicates desired changes to the structure or focus of mesocycles, such as shifting phases or changing durations."
    )
    detail: Optional[str] = Field(
        None, description="Specific requests such as 'add a strength phase after hypertrophy' or 'reduce deload to 1 week'."
    )

# Model to extract goal information for the Microcycle from user input.
class MicrocycleGoal(BaseModel):
    """Goal extraction from user input regarding user microcycles."""
    is_requested: bool = Field(
        ..., description="True if the user wants to adjust their microcycle (weekly) structure, e.g., number of training days or workout frequency."
    )
    detail: Optional[str] = Field(
        None, description="Requested changes such as 'train 4 days per week' or 'add a rest day midweek'."
    )

# Model to extract goal information for the Phase Component from user input.
class PhaseComponentGoal(BaseModel):
    """Goal extraction from user input regarding user phase components."""
    is_requested: bool = Field(
        ..., description="True if the user wants to modify the distribution of phase components (e.g., hypertrophy, strength, endurance) within a microcycle."
    )
    detail: Optional[str] = Field(
        None, description="Details like 'replace strength with hypertrophy on Thursday' or 'more focus on power training in this microcycle'."
    )

# Model to extract goal information for the Workout Schedule from user input.
class WorkoutScheduleGoal(BaseModel):
    """Goal extraction from user input regarding user workout schedules."""
    is_requested: bool = Field(
        ..., description="True if the user wants to directly modify the exercises or structure of specific workouts."
    )
    detail: Optional[str] = Field(
        None, description="Workout-specific updates like 'replace squats with lunges on leg day' or 'add more core work on Tuesday'."
    )

# Model to extract goal information for the WorkoutCompletion from user input.
class WorkoutCompletionGoal(BaseModel):
    """Goal extraction from user input regarding user workout completion."""
    is_requested: bool = Field(
        ..., description="True if the has completed their workout."
    )
    detail: Optional[str] = Field(
        None, description="Details like if the user only completed part of their workout."
    )

# Model to extract goal information for the exercise routine from user input.
class RoutineImpactGoals(BaseModel):
    """Hierarchical goal extraction from user input regarding exercise routine."""
    availability: AvailabilityGoal
    macrocycle: MacrocycleGoal
    mesocycle: MesocycleGoal
    microcycle: MicrocycleGoal
    phase_component: PhaseComponentGoal
    workout_schedule: WorkoutScheduleGoal
    workout_completion: WorkoutCompletionGoal