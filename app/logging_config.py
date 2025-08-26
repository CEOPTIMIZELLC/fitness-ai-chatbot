import logging
from functools import partial

from flask import current_app

verbosity_config = current_app.config["VERBOSITY_CONFIG"]
DatabaseInitVerbosityConfig = verbosity_config.DatabaseInit
RouteVerbosityConfig = verbosity_config.Route
MainAgentVerbosityConfig = verbosity_config.MainAgent
MainSubAgentVerbosityConfig = verbosity_config.MainSubAgent
SchedulerPreProcessingVerbosityConfig = verbosity_config.SchedulerPreProcessing
SchedulerVerbosityConfig = verbosity_config.Scheduler

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
    if enabled and verbosity_config.verbose:
        # logger.log(level, message)
        log_long_output(level, message)

# Partial Functions for Each Verbosity Type
log_verbose = partial(verbose_log, verbosity_config.verbose)

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
    agent_output = partial(verbose_log, MainAgentVerbosityConfig.agent_output)
    input_info = partial(verbose_log, MainAgentVerbosityConfig.input_info)
    system_message = partial(verbose_log, MainAgentVerbosityConfig.system_message)
    formatted_schedule = partial(verbose_log, MainAgentVerbosityConfig.formatted_schedule)

class LogMainSubAgent:
    verbose = partial(verbose_log, MainSubAgentVerbosityConfig.verbose)
    agent_introductions = partial(verbose_log, MainSubAgentVerbosityConfig.agent_introductions)
    agent_steps = partial(verbose_log, MainSubAgentVerbosityConfig.agent_steps)
    agent_output = partial(verbose_log, MainSubAgentVerbosityConfig.agent_output)
    parsed_goal = partial(verbose_log, MainSubAgentVerbosityConfig.parsed_goal)
    input_info = partial(verbose_log, MainSubAgentVerbosityConfig.input_info)
    system_message = partial(verbose_log, MainSubAgentVerbosityConfig.system_message)
    formatted_schedule = partial(verbose_log, MainSubAgentVerbosityConfig.formatted_schedule)

class LogSolverPreProcessing:
    verbose = partial(verbose_log, SchedulerPreProcessingVerbosityConfig.verbose)
    exercises_for_pc_steps = partial(verbose_log, SchedulerPreProcessingVerbosityConfig.exercises_for_pc_steps)

class LogSolver:
    verbose = partial(verbose_log, SchedulerVerbosityConfig.verbose)
    agent_time = partial(verbose_log, SchedulerVerbosityConfig.agent_time)
    agent_steps = partial(verbose_log, SchedulerVerbosityConfig.agent_steps)
    agent_output = partial(verbose_log, SchedulerVerbosityConfig.agent_output)
    formatted_schedule = partial(verbose_log, SchedulerVerbosityConfig.formatted_schedule)
