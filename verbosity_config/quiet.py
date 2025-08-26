from .base import *

# Logging configurations options for the database initialization.
class DatabaseInitVerbosityConfig(DatabaseInitVerbosityConfigBase):
    verbose = False
    introductions = False
    clustering = False
    data_errors = False

# Logging configurations options for the routes.
class RouteVerbosityConfig(RouteVerbosityConfigBase):
    verbose = False

# Logging configurations options for the main agent.
class MainAgentVerbosityConfig(MainAgentVerbosityConfigBase):
    verbose = False
    agent_introductions = False
    agent_steps = False
    agent_output = False
    input_info = False
    system_message = False
    formatted_schedule = False

# Logging configurations options for the main sub agents.
class MainSubAgentVerbosityConfig(MainSubAgentVerbosityConfigBase):
    verbose = False
    agent_introductions = False
    agent_steps = False
    agent_output = False
    input_info = False
    system_message = False
    parsed_goal = False
    formatted_schedule = False

# Logging configurations options for the solver preprocessing verbosity.
class SchedulerPreProcessingVerbosityConfig(SchedulerPreProcessingVerbosityConfigBase):
    verbose = False
    exercises_for_pc_steps = False

# Logging configurations options for the solver agent verbosity.
class SchedulerVerbosityConfig(SchedulerVerbosityConfigBase):
    verbose = False
    agent_time = False
    agent_steps = False
    agent_output = False
    formatted_schedule = False

# Logging configurations for general application.
class VerbosityConfig(VerbosityConfigBase):
    verbose = False
    DatabaseInit = DatabaseInitVerbosityConfig
    Route = RouteVerbosityConfig
    MainAgent = MainAgentVerbosityConfig
    MainSubAgent = MainSubAgentVerbosityConfig
    SchedulerPreProcessing = SchedulerPreProcessingVerbosityConfig
    Scheduler = SchedulerVerbosityConfig
