# fitness-ai-chatbot
AI based personal trainer with ability to chat with clients to build and maintain personalized programs and daily workouts.

# Setup
Ensure that you have an environment file with the following environment variables filled out at the route level.

## Environment Variables
```bash
POSTRGRES_HOST="localhost"
POSTRGRES_DATABASE="fitness_db"
POSTRGRES_USER="postgres"
POSTRGRES_PASSWORD="postgres"

EMBEDDING_MODEL="text-embedding-3-small"
LANGUAGE_MODEL="gpt-4o-mini"
OPENAI_API_KEY=
```

## Configuration Variables
```bash
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
```

***

# How to Run
```bash
poetry run python run.py
```

***

## Set Up Database
**Initialize Database (If you want to reset the database)**
Ideally done after logging out.
```
[POST]
localhost:5000/database_manipulation/init_db
```

***

## User Authentication
**Register User**
```
[POST]
localhost:5000/database_manipulation/init_db

BODY (form-data):
email: [string; REQUIRED; Must be a valid email address format that doesn't already exist in the database]
password: [string; REQUIRED; Must be between 8 and 20 characters long, must contain at least one number, and must contain at least one of the following characters: ! @ # $ % ^ & * _ ?]
password_confirm: [string; REQUIRED; Must be the same as password]
first_name: [string; REQUIRED;]
last_name: [string; REQUIRED;]
age: [int; REQUIRED;]
gender: [string; REQUIRED;]
goal: [string; REQUIRED;]
```

**Login User**
```
[POST]
localhost:5000/login

BODY (form-data):
email: [string; REQUIRED; Must be a valid email address that exists in the database]
password: [string; REQUIRED; Must be the same as the password that was used to register the user with the given email address.]
```

**Logout User (If logged in)**
```
[POST]
localhost:5000/logout
```

***

## Test Main Agent 
(Perform after registering user and logging in.)

**Enter Main Agent (If logged in)**
```
[POST, PATCH]
localhost:5000/main_agent/enter
```

**Test User Input (If logged in; AFTER entering the agent)**
```
[POST, PATCH]
localhost:5000/main_agent/resume

BODY (raw) [JSON]:
{
    "user_input": "[string; REQUIRED; Message to be parsed by the agent to determine which goals to perform.]"
}
```

**Delete Old Schedules (If logged in)**
```
[DELETE]
localhost:5000/main_agent
```

**Enter Main Agent and Test User Input (If logged in)**
```
[POST, PATCH]
localhost:5000/main_agent

BODY (raw) [JSON]:
{
    "user_input": "[string; REQUIRED; Message to be parsed by the agent to determine which goals to perform.]"
}
```

**Delete Old Schedules, Enter Main Agent, and Test User Input (If logged in)**
```
[POST, PATCH]
localhost:5000/main_agent/clean

BODY (raw) [JSON]:
{
    "user_input": "[string; REQUIRED; Message to be parsed by the agent to determine which goals to perform.]"
}
```

***

# Routes To Run
## Quick Run Steps
**Logout User (If logged in)**
```
[POST]
localhost:5000/logout
```

**Initialize Database with User (If you want to reset the database)**
```
[POST]
localhost:5000/database_manipulation/init_db

BODY (form-data):
email: [string; REQUIRED; Must be a valid email address format that doesn't already exist in the database]
password: [string; REQUIRED; Must be between 8 and 20 characters long, must contain at least one number, and must contain at least one of the following characters: ! @ # $ % ^ & * _ ?]
password_confirm: [string; REQUIRED; Must be the same as password]
first_name: [string; REQUIRED;]
last_name: [string; REQUIRED;]
age: [int; REQUIRED;]
gender: [string; REQUIRED;]
goal: [string; REQUIRED;]
```

**Login User**
```
[POST]
localhost:5000/login

BODY (form-data):
email: [string; REQUIRED; Must be a valid email address that exists in the database]
password: [string; REQUIRED; Must be the same as the password that was used to register the user with the given email address.]
```

**Enter Main Agent**
```
[POST, PATCH]
localhost:5000/main_agent/enter
```

**Test User Input**
```
[POST, PATCH]
localhost:5000/main_agent/resume

BODY (raw) [JSON]:
{
    "user_input": "[string; REQUIRED; Message to be parsed by the agent to determine which goals to perform.]"
}
```

***

## Example Fields
**Logout User (If logged in)**
```
[POST]
localhost:5000/logout
```

**Initialize Database with User (If you want to reset the database)**
```
[POST]
localhost:5000/database_manipulation/init_db

BODY (form-data):
    email: email2@gmail.com
    password: password?2
    password_confirm: password?2
    first_name: Debra
    last_name: Grey
    age: 20
    gender: female
    goal: "I want to increase my upper body strength."
```

**Login User**
```
[POST]
localhost:5000/login

BODY (form-data):
    email: email2@gmail.com
    password: password?2
```


**Enter Main Agent**
```
[POST, PATCH]
localhost:5000/main_agent/enter
```

**Test User Input**
```
[POST]
localhost:5000/dev_tests/pipeline

BODY (raw) [JSON]:
{
    "user_input": "I want to train four times a week instead of three, and can we swap squats for leg press on leg day? I should have 30 minutes every day now. My goal to prepare for my soccer tournament. I would like you to schedule the mesoscycles, microcycles, the phase components, and the workouts as well."
}
```
