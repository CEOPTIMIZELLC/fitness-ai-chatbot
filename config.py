import os
import load_env_var
from datetime import timedelta

agent_recursion_limit = 30
distance_threshold = 1.1
user_equipment_population_default = 2
ortools_solver_time_in_seconds = 5
vertical_loading = True
loop_main_agent = True

# Configurations for exercise performance decay.
class ExercisePerformanceDecayConfig:
    grace_period = 14
    decay_rate = -0.05
    exponential_decay = True

# Configurations for exercise performance decay.
class ExerciseOneRepMaxDecayConfig:
    grace_period = 14
    decay_rate = -0.05
    exponential_decay = True

# Configurations for verbose options.
verbose = True

# Configurations for verbose options.
class VerbosityConfig:
    verbose = True
    existing_data_errors = True

# Configurations options for the routes.
class RouteVerbosityConfig:
    verbose = True

# Configurations options for the main agent.
class MainAgentVerbosityConfig:
    verbose = True
    agent_introductions = True
    agent_steps = True
    agent_output = True
    input_info = True
    formatted_schedule = True

# Configurations options for the main sub agents.
class MainSubAgentVerbosityConfig:
    verbose = True
    agent_introductions = True
    agent_steps = True
    agent_output = True
    parsed_goal = True
    formatted_schedule = True

# Configurations options for the solver preprocessing verbosity.
class SchedulerPreProcessingVerbosityConfig:
    verbose = True
    exercises_for_pc_steps = True

# Configurations options for the solver agent verbosity.
class SchedulerVerbosityConfig:
    verbose = True
    agent_time = True
    agent_steps = True
    agent_output = True
    formatted_schedule = True

# Configurations for agent logging.
class SchedulerLoggingConfig:
    schedule = True
    agent_steps = True
    counts = True
    constraints = True
    details = True

# Configuration for phase components to be removed.
change_min_max_exercises_for_those_available = True
turn_off_invalid_phase_components = True
turn_off_required_resistances = True

# Configurations for exerecises to be included for phase components upon initial failure.
class BackupExerciseRetrieval:
    for_desired_full_body = True
    for_desired_bodypart = True
    for_desired_phase_component = False
    all_exercises = False

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://'+os.environ["POSTRGRES_USER"]+':'+os.environ["POSTRGRES_PASSWORD"]+'@'+os.environ["POSTRGRES_HOST"]+'/'+os.environ["POSTRGRES_DATABASE"]
    LANGUAGE_MODEL = os.environ.get("LANGUAGE_MODEL")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
    #PERMANENT_SESSION_LIFETIME = timedelta(minutes=1)