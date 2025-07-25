import logging
from functools import partial

from config import VerbosityConfig

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