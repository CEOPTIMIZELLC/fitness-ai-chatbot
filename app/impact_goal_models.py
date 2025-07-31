from pydantic import BaseModel, Field
from typing import Optional

from .user_weekdays_availability import AvailabilityGoal
from .user_macrocycles import MacrocycleGoal
from .user_mesocycles import MesocycleGoal
from .user_microcycles import MicrocycleGoal
from .user_workout_days import PhaseComponentGoal
from .user_workout_exercises import WorkoutScheduleGoal
from .user_workout_completion import WorkoutCompletionGoal

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