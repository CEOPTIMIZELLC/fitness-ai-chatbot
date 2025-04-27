from datetime import timedelta

DEFAULT_WORKOUT_LENGTH = timedelta(hours=1)
DEFAULT_MACROCYCLE_LENGTH = timedelta(weeks=26)
DEFAULT_MESOCYCLE_LENGTH = timedelta(weeks=4)
DEFAULT_MICROCYCLE_LENGTH = timedelta(weeks=1)

STRAIN_MULTIPLIER = 0.1  # Used in strain calculations (1 + base_strain / 10)