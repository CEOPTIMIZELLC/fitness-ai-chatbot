import os
import load_env_var
from datetime import timedelta

user_equipment_population_default = 2
ortools_solver_time_in_seconds = 5
vertical_loading = True

# Configurations for exercise performance decay.
performance_decay_grace_period = 10

## Linear decay if False.
exponential_decay = True

# Configurations for verbose options.
verbose = True
verbose_agent_preprocessing = True
verbose_exercises_for_pc_steps = False
verbose_agent_time = True
verbose_agent_steps = True

# Configurations for agent logging.
log_schedule = True
log_counts = True
log_constraints = True
log_details = True

# Configuration for phase components to be removed.
change_min_max_exercises_for_those_available = True
turn_off_invalid_phase_components = True
turn_off_required_resistances = True

# Configurations for exerecises to be included for phase components upon initial failure.
include_all_exercises_for_desired_full_body = True
include_all_exercises_for_desired_bodypart = True
incude_all_exercises_for_desired_phase_component = False
include_all_exercises = False

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://'+os.environ["POSTRGRES_USER"]+':'+os.environ["POSTRGRES_PASSWORD"]+'@'+os.environ["POSTRGRES_HOST"]+'/'+os.environ["POSTRGRES_DATABASE"]
    LANGUAGE_MODEL = os.environ.get("LANGUAGE_MODEL")
    #PERMANENT_SESSION_LIFETIME = timedelta(minutes=1)