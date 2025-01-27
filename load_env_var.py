import os
from dotenv import load_dotenv, find_dotenv

# Loads the environment variables.
load_dotenv(find_dotenv())

# Returns value from corresponding environment variable key.
# Returns an error if environment variable isn't present.
def environment_variable_retrieve(env_var_key):
    env_var_value = os.getenv(env_var_key)
    if not env_var_value:
        raise ValueError(env_var_value+" not found in environment variables.")
    return env_var_value

class postgresBase:
    def __init__(self):
        # Load postrgres environment variables.
        os.environ["POSTRGRES_HOST"] = environment_variable_retrieve("POSTRGRES_HOST")
        os.environ["POSTRGRES_DATABASE"] = environment_variable_retrieve("POSTRGRES_DATABASE")
        os.environ["POSTRGRES_USER"] = environment_variable_retrieve("POSTRGRES_USER")
        os.environ["POSTRGRES_PASSWORD"] = environment_variable_retrieve("POSTRGRES_PASSWORD")