from .base import VerbosityConfigBase
from .base import SchedulerPreProcessingVerbosityConfigBase as BaseConfig

# Logging configurations options for the solver preprocessing verbosity.
class SchedulerPreProcessingVerbosityConfig(BaseConfig):
    verbose = True
    exercises_for_pc_steps = True

# Logging configurations for general application.
class VerbosityConfig(VerbosityConfigBase):
    SchedulerPreProcessing = SchedulerPreProcessingVerbosityConfig