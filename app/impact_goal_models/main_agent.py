from pydantic import BaseModel, Field
from typing import Optional

from .availability import AvailabilityGoalPart
from .equipment import EquipmentGoalPart
from .macrocycles import MacrocycleGoalPart
from .mesocycles import MesocycleGoalPart
from .microcycles import MicrocycleGoalPart
from .phase_components import PhaseComponentGoalPart
from .workout_schedule import WorkoutScheduleGoalPart
from .workout_completion import WorkoutCompletionGoalPart

# Model to extract goal information for the exercise routine from user input.
class RoutineImpactGoals(BaseModel):
    """Hierarchical goal extraction from user input regarding exercise routine."""
    availability: AvailabilityGoalPart
    macrocycle: MacrocycleGoalPart
    mesocycle: MesocycleGoalPart
    microcycle: MicrocycleGoalPart
    phase_component: PhaseComponentGoalPart
    workout_schedule: WorkoutScheduleGoalPart
    workout_completion: WorkoutCompletionGoalPart
    equipment: EquipmentGoalPart