from .base import VerbosityConfigBase
from .base import MainAgentVerbosityConfigBase as BaseConfig

# Logging configurations options for the main agent.
class MainAgentVerbosityConfig(BaseConfig):
    verbose = True
    agent_introductions = True
    agent_steps = True
    agent_output = True
    input_info = True
    system_message = True
    formatted_schedule = True

# Logging configurations for general application.
class VerbosityConfig(VerbosityConfigBase):
    MainAgent = MainAgentVerbosityConfig