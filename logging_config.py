import logging
from functools import partial

from config import VerbosityConfig, SchedulerVerbosityConfig, SchedulerPreProcessingVerbosityConfig

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
log_existing_data_errors = partial(verbose_log, VerbosityConfig.existing_data_errors)

class LogSolverPreProcessing:
    verbose = partial(verbose_log, SchedulerPreProcessingVerbosityConfig.verbose)
    exercises_for_pc_steps = partial(verbose_log, SchedulerPreProcessingVerbosityConfig.exercises_for_pc_steps)

class LogSolver:
    verbose = partial(verbose_log, SchedulerVerbosityConfig.verbose)
    agent_time = partial(verbose_log, SchedulerVerbosityConfig.agent_time)
    agent_steps = partial(verbose_log, SchedulerVerbosityConfig.agent_steps)
    agent_output = partial(verbose_log, SchedulerVerbosityConfig.agent_output)
    formatted_schedule = partial(verbose_log, SchedulerVerbosityConfig.formatted_schedule)
