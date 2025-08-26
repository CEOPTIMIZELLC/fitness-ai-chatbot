from .base import (
    VerbosityConfigBase, 
    DatabaseInitVerbosityConfigBase, 
    RouteVerbosityConfigBase, 
)

from .main_agent import MainAgentVerbosityConfig
from .main_sub_agent import MainSubAgentVerbosityConfig
from .scheduler import SchedulerVerbosityConfig
from .scheduler_pre_processing import SchedulerPreProcessingVerbosityConfig

# Logging configurations options for the database initialization.
class DatabaseInitVerbosityConfig(DatabaseInitVerbosityConfigBase):
    verbose = True
    introductions = True
    clustering = True
    data_errors = True

# Logging configurations options for the routes.
class RouteVerbosityConfig(RouteVerbosityConfigBase):
    verbose = True

# Logging configurations for general application.
class VerbosityConfig(VerbosityConfigBase):
    verbose = True
    DatabaseInit = DatabaseInitVerbosityConfig
    Route = RouteVerbosityConfig
    MainAgent = MainAgentVerbosityConfig
    MainSubAgent = MainSubAgentVerbosityConfig
    SchedulerPreProcessing = SchedulerPreProcessingVerbosityConfig
    Scheduler = SchedulerVerbosityConfig
