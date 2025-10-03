import logging
from functools import partial

from config import (
    VerbosityConfig, 
    RouteVerbosityConfig, 
    DatabaseInitVerbosityConfig, 
    MainAgentVerbosityConfig, 
    MainSubAgentVerbosityConfig, 
    ParentAgentVerbosityConfig, 
    AlteringAgentVerbosityConfig, 
    CreationAgentVerbosityConfig, 
    DeletionAgentVerbosityConfig, 
    ReadingAgentVerbosityConfig, 
    EditorAgentVerbosityConfig, 
    SchedulerVerbosityConfig, 
    SchedulerPreProcessingVerbosityConfig
)

# Set Up the Logger
logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)  # Log everything, but filter via verbosity config

# Console handler
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
# formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_long_output(level, message):
    for line in message.strip().split('\n'):
        logger.log(level, line)
    return None

# Verbose Logging Utility
def verbose_log(enabled: bool, message: str, level=logging.INFO):
    if enabled and VerbosityConfig.verbose:
        # logger.log(level, message)
        log_long_output(level, message)

# Partial Functions for Each Verbosity Type
log_verbose = partial(verbose_log, VerbosityConfig.verbose)

class LogGeneral:
    verbose = partial(verbose_log, VerbosityConfig.verbose)
    other_request_updates = partial(verbose_log, VerbosityConfig.other_request_updates)
    system_message = partial(verbose_log, VerbosityConfig.system_message)
    human_message = partial(verbose_log, VerbosityConfig.human_message)
    parsed_goal = partial(verbose_log, VerbosityConfig.parsed_goal)

class LogRoute:
    verbose = partial(verbose_log, RouteVerbosityConfig.verbose)

class LogDBInit:
    verbose = partial(verbose_log, DatabaseInitVerbosityConfig.verbose)
    introductions = partial(verbose_log, DatabaseInitVerbosityConfig.introductions)
    clustering = partial(verbose_log, DatabaseInitVerbosityConfig.clustering)
    data_errors = partial(verbose_log, DatabaseInitVerbosityConfig.data_errors)

class LogMainAgent:
    verbose = partial(verbose_log, MainAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, MainAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, MainAgentVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, MainAgentVerbosityConfig.formatted_schedule)

class LogMainSubAgent:
    verbose = partial(verbose_log, MainSubAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, MainSubAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, MainSubAgentVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, MainSubAgentVerbosityConfig.formatted_schedule)
    agent_path = partial(verbose_log, MainSubAgentVerbosityConfig.agent_path)

class LogParentSubAgent:
    verbose = partial(verbose_log, ParentAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, ParentAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, ParentAgentVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, ParentAgentVerbosityConfig.formatted_schedule)
    agent_path = partial(verbose_log, ParentAgentVerbosityConfig.agent_path)

class LogAlteringAgent:
    verbose = partial(verbose_log, AlteringAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, AlteringAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, AlteringAgentVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, AlteringAgentVerbosityConfig.formatted_schedule)

class LogCreationAgent:
    verbose = partial(verbose_log, CreationAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, CreationAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, CreationAgentVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, CreationAgentVerbosityConfig.formatted_schedule)

class LogDeletionAgent:
    verbose = partial(verbose_log, DeletionAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, DeletionAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, DeletionAgentVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, DeletionAgentVerbosityConfig.formatted_schedule)

class LogReadingAgent:
    verbose = partial(verbose_log, ReadingAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, ReadingAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, ReadingAgentVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, ReadingAgentVerbosityConfig.formatted_schedule)

class LogEditorAgent:
    verbose = partial(verbose_log, EditorAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, EditorAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, EditorAgentVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, EditorAgentVerbosityConfig.formatted_schedule)

class LogSolverPreProcessing:
    verbose = partial(verbose_log, SchedulerPreProcessingVerbosityConfig.verbose)
    exercises_for_pc_steps = partial(verbose_log, SchedulerPreProcessingVerbosityConfig.exercises_for_pc_steps)

class LogSolver:
    verbose = partial(verbose_log, SchedulerVerbosityConfig.verbose)
    agent_time = partial(verbose_log, SchedulerVerbosityConfig.agent_time)
    agent_steps = partial(verbose_log, SchedulerVerbosityConfig.agent_steps)
    formatted_schedule = partial(verbose_log, SchedulerVerbosityConfig.formatted_schedule)
