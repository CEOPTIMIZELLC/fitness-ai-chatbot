import os
import load_env_var
from datetime import timedelta

# How many iterations of a loop are allowed before some interruption.
agent_recursion_limit = 30

# Distance threshold for if semantic clustering of exercises (smaller number means more precise).
distance_threshold = 1.1

# If a dummy user is created in the database initialization, which preset for equipment to be included.
# [1-3]
user_equipment_population_default = 2

# The maximum number of seconds that the solver is allowed to take on default.
ortools_solver_time_in_seconds = 5

# Whether the workout schedule will use vertical loading.
vertical_loading = True

# Whether the main agent will loop after finishing.
loop_main_agent = True

# Configurations for exercise performance decay.
class ExercisePerformanceDecayConfig:
    # The number of days before the performance of an exercise will begin to decay.
    grace_period = 14

    # The rate at which the performance will decay after the grace period.
    decay_rate = -0.05

    # Whether the rate of decay will be exponential (linear decay if false).
    exponential_decay = True

# Configurations for exercise performance decay.
class ExerciseOneRepMaxDecayConfig:
    # The number of days before the 1RM of an exercise will begin to decay.
    grace_period = 14

    # The rate at which the 1RM will decay after the grace period.
    decay_rate = -0.05

    # Whether the rate of decay will be exponential (linear decay if false).
    exponential_decay = True

# General option for verbose logging.
verbose = True

# Logging configurations for general application.
class VerbosityConfig:
    # Log results throughout project.
    verbose = True

    # Log if an error occurs in the initial database population.
    existing_data_errors = True

# Logging configurations options for the routes.
class RouteVerbosityConfig:
    # Log route outputs.
    verbose = True

# Logging configurations options for the main agent.
class MainAgentVerbosityConfig:
    # Log any items in this configuration set.
    verbose = True

    # Log introduction and end for the main agent.
    agent_introductions = True

    # Log node introductions in the main agent.
    agent_steps = True

    # Log the output of main agent.
    agent_output = True

    # Log information regarding user input in the main agent.
    input_info = True

    # Log final formatted schedule produced.
    formatted_schedule = True

# Logging configurations options for the main sub agents.
class MainSubAgentVerbosityConfig:
    # Log any items in this configuration set.
    verbose = True

    # Log introduction and end for the sub agents.
    agent_introductions = True

    # Log node introductions in the sub agents.
    agent_steps = True

    # Log the output of the sub agents.
    agent_output = True

    # Log the parsed user input for the sub agents.
    parsed_goal = True

    # Log final formatted schedule produced.
    formatted_schedule = True

# Logging configurations options for the solver preprocessing verbosity.
class SchedulerPreProcessingVerbosityConfig:
    # Log any items in this configuration set.
    verbose = True

    # Log ALL steps taken when finding the exercises for phase components.
    exercises_for_pc_steps = True

# Logging configurations options for the solver agent verbosity.
class SchedulerVerbosityConfig:
    # Log any items in this configuration set.
    verbose = True

    # Log the time taken for an agent to be completed will be printed.
    agent_time = True

    # Log node introductions in the solver agents.
    agent_steps = True

    # Log the output of the solver agents.
    agent_output = True

    # Log final formatted schedule produced.
    formatted_schedule = True

# Configurations for agent logging.
class SchedulerLoggingConfig:
    # Add the schedule itself to the logged output.
    schedule = True

    # Add the node introductions to the logged output.
    agent_steps = True

    # Add the number of elements included in the schedule to the logged output.
    counts = True

    # Add the final constraints used by the solver to the logged output.
    constraints = True

    # Add the values relevant to the schedule (total time, total strain) to the logged output.
    details = True

# Configuration for phase components to be removed.
change_min_max_exercises_for_those_available = True
turn_off_invalid_phase_components = True
turn_off_required_resistances = True

# Configurations for exerecises to be included for phase components upon initial failure.
# When determining what exercises are allowed for a phase component, 
# various options can be taken to attempt to fill in exercises. The 
# configurations will not be applied all at once, but will rather 
# be carried out in order: 
# (if no exercises are found --> look for all exercises for full body --> if no exercises are found, look for all exercises for the bodypart)
class BackupExerciseRetrieval:
    # All exercises for the phase component will be included if the bodypart is full body.
    for_desired_full_body = True

    # All exercises for the desired bodypart will be included.
    for_desired_bodypart = True

    # All exercises for the desired phase compoent will be included.
    for_desired_phase_component = False

    # All exercises in the database will be inlcuded.
    all_exercises = False

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://'+os.environ["POSTRGRES_USER"]+':'+os.environ["POSTRGRES_PASSWORD"]+'@'+os.environ["POSTRGRES_HOST"]+'/'+os.environ["POSTRGRES_DATABASE"]
    LANGUAGE_MODEL = os.environ.get("LANGUAGE_MODEL")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
    #PERMANENT_SESSION_LIFETIME = timedelta(minutes=1)