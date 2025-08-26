from .base import VerbosityConfigBase
from .base import MainSubAgentVerbosityConfigBase as BaseConfig

# Logging configurations options for the main sub agents.
class MainSubAgentVerbosityConfig(BaseConfig):
    verbose = True
    agent_introductions = True
    agent_steps = True
    agent_output = True
    input_info = True
    system_message = True
    parsed_goal = True
    formatted_schedule = True

# Logging configurations for general application.
class VerbosityConfig(VerbosityConfigBase):
    MainSubAgent = MainSubAgentVerbosityConfig