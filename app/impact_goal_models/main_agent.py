from pydantic import BaseModel, Field
from typing import Optional

from .availability import AvailabilityGoal
from .macrocycles import MacrocycleGoal
from .mesocycles import MesocycleGoal
from .microcycles import MicrocycleGoal
from .phase_components import PhaseComponentGoal
from .workout_schedule import WorkoutScheduleGoal
from .workout_completion import WorkoutCompletionGoal

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