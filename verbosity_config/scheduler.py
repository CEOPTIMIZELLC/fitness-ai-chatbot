from .base import VerbosityConfigBase
from .base import SchedulerVerbosityConfigBase as BaseConfig

# Logging configurations options for the solver agent verbosity.
class SchedulerVerbosityConfig(BaseConfig):
    verbose = True
    agent_time = True
    agent_steps = True
    agent_output = True
    formatted_schedule = True

# Logging configurations for general application.
class VerbosityConfig(VerbosityConfigBase):
    Scheduler = SchedulerVerbosityConfig