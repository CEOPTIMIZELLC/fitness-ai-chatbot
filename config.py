import os
import load_env_var
from datetime import timedelta

ortools_solver_time_in_seconds = 5
verbose = True
log_steps = True
log_details = True

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://'+os.environ["POSTRGRES_USER"]+':'+os.environ["POSTRGRES_PASSWORD"]+'@'+os.environ["POSTRGRES_HOST"]+'/'+os.environ["POSTRGRES_DATABASE"]
    LANGUAGE_MODEL = os.environ.get("LANGUAGE_MODEL")
    #PERMANENT_SESSION_LIFETIME = timedelta(minutes=1)