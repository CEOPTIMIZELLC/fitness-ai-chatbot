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

LANGUAGE_MODEL="gpt-4o-mini"
OPENAI_API_KEY=
```

## Configuration Variables
```bash
user_equipment_population_default = [1-3]                   # If a dummy user is created in the database initialization, there are three presets for equipment to be included, each including more equipment and more varieties of measurements.
ortools_solver_time_in_seconds = 5                          # The maximum number of seconds that the solver is allowed to take on default.
vertical_loading = True                                     # Whether the workout schedule will use vertical loading.

# Configurations for exercise performance decay.
performance_decay_grace_period = 14                         # The number of days before the performance of an exercise will begin to decay.
performance_decay_rate = -0.05                              # The rate at which the performance will decay after the grace period.
one_rep_max_decay_grace_period = 14                         # The number of days before the 1RM of an exercise will begin to decay.
one_rep_max_decay_rate = -0.05                              # The rate at which the 1RM will decay after the grace period.
exponential_decay = True                                    # Whether the rate of decay will be exponential (linear decay if false).

# Configurations for verbose options.
verbose = True                                              # Print various messages throughout project.
verbose_agent_preprocessing = True                          # Whether the various steps taken before the agent processing (time correction, exercises for phase components) will be printed.
verbose_exercises_for_pc_steps = False                      # Whether ALL of the steps taken when finding the exercises for phase components will be printed.
verbose_agent_time = True                                   # Whether the time taken for an agent to be completed will be printed.
verbose_agent_steps = True                                  # Whether the current steps for the agent will be printed as they are reached.

# Configurations for agent logging (the schedule printed).
log_schedule = True                                         # Log the schedule itself.
log_counts = True                                           # Log the number of elements included in the schedule.
log_constraints = True                                      # Log the final constraints used by the solver.
log_details = True                                          # Log the values relevant to the schedule (total time, total strain).

# Configuration for phase components to be removed during preprocessing.
change_min_max_exercises_for_those_available = True         # If a phase component has fewer exercises available to it than the minimum required, change the minimum and maximum to the be quantity available.
turn_off_invalid_phase_components = True                    # If a phase component is completely impossible, turn it off as required.
turn_off_required_resistances = True                        # If a required resistance phase component is completely impossible, turn it off.


# Configuration for exerecise inclusion for phase components upon initial failure. 
# When determining what exercises are allowed for a phase component, 
# various options can be taken to attempt to fill in exercises. The 
# configurations will not be applied all at once, but will rather 
# be carried out in order: 
# (if no exercises are found --> look for all exercises for full body --> if no exercises are found, look for all exercises for the bodypart)`
include_all_exercises_for_desired_full_body = True          # All exercises for the phase component will be included if the bodypart is full body.
include_all_exercises_for_desired_bodypart = True           # All exercises for the desired bodypart will be included.
incude_all_exercises_for_desired_phase_component = False    # All exercises for the desired phase compoent will be included.
include_all_exercises = False                               # All exercises in the database will be inlcuded.
```

# Database Initial Setup
If significant changes have been made to the models, it may be necessary to run the following from the parent directory to restart the database. As of right now, if you remove models that map to tables that would have foreign keys that rely on it, the code may not be able to drop them from the database with the current restarting route in the application. To get around this, a script has been created that will simply delete the old database and make a new empty one that can be used. 
```bash
poetry run python reinitialize_db_script.py
```

# How to Run
```bash
poetry run python run.py
```

# Routes To Run
## Run Steps
**Logout User (If logged in)**
```
[POST]
localhost:5000/logout
```

**Initialize Database (If you want to reset the database)**
```
[POST]
localhost:5000/database_manipulation/init_db
```

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

**Set Availability for Each Weekday**
```
[POST]
localhost:5000/user_weekday_availability/

BODY (raw) [JSON]:
{
    "availability": "[string; REQUIRED; Message to send to the AI to extract your availability for each weekday.]"
}
```

**Set Current Goal/Create New Macrocycle**
```
[POST]
localhost:5000/user_macrocycles/

BODY (raw) [JSON]:
{
    "goal": "[string; REQUIRED; Message to send to the AI to extract your current goal and determine its type.]"
}
```

**Assign Phase Components to the Current Macrocycle/Create Mesocycles for the Current Macrocycle**
```
[POST]
localhost:5000/user_mesocycles/
```

**Create a Microcycle for Each Week in the Current Mesocycle/Create Microcycles for the Current Mesocycle**
```
[POST]
localhost:5000/user_microcycles/
```

**Determine which phase components to assign to each day in the microcycle/Create Workout Days for the Current Microcycle**
```
[POST]
localhost:5000/user_workout_days/
```

**Determine which exercises to assign to each phase component in each day in the microcycle/Create Exercises for the Current Workout Days**
```
[POST]
localhost:5000/user_workout_exercises/
```

**Indicate that the workout has been completed/Update User Exercises**
```
[POST]
localhost:5000/user_workout_exercises/complete_workout
```


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

**Run Pipeline**
```
[POST]
localhost:5000/dev_tests/pipeline

BODY (raw) [JSON]:
{
    "availability": "[string; REQUIRED; Message to send to the AI to extract your availability for each weekday.]",
    "goal": "[string; REQUIRED; Message to send to the AI to extract your current goal and determine its type.]"
}
```

***
# Example Fields
## Example Run
**Logout User (If logged in)**
```
[POST]
localhost:5000/logout
```

**Initialize Database (If you want to reset the database)**
```
[POST]
localhost:5000/database_manipulation/init_db
```

**Register User**
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

**Set Availability for Each Weekday**
```
[POST]
localhost:5000/user_weekday_availability/

BODY (raw) [JSON]:
{
    "availability": "I will be available for 35 minutes on Tuesday, 30 minutes on Thurday, 45 minutes on Wednesday and Friday, and 12 hours on Sunday. I will also be able to come on Monday for 14 hours."
}
```

**Set Current Goal/Create New Macrocycle**
```
[POST]
localhost:5000/user_macrocycles/

BODY (raw) [JSON]:
{
    "goal": "I would like to prepare for my soccer tournament."
}
```

**Assign Phase Components to the Current Macrocycle/Create Mesocycles for the Current Macrocycle**
```
[POST]
localhost:5000/user_mesocycles/
```

**Create a Microcycle for Each Week in the Current Mesocycle/Create Microcycles for the Current Mesocycle**
```
[POST]
localhost:5000/user_microcycles/
```

**Determine which phase components to assign to each day in the microcycle/Create Workout Days for the Current Microcycle**
```
[POST]
localhost:5000/user_workout_days/
```

**Determine which exercises to assign to each phase component in each day in the microcycle/Create Exercises for the Current Workout Days**
```
[POST]
localhost:5000/user_workout_exercises/
```

**Indicate that the workout has been completed/Update User Exercises**
```
[POST]
localhost:5000/user_workout_exercises/complete_workout
```


## Example Quick Run
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

**Run Pipeline**
```
[POST]
localhost:5000/dev_tests/pipeline

BODY (raw) [JSON]:
{
    "goal": "I would like to prepare for my soccer tournament.",
    "availability": "I will be available for 35 minutes on Tuesday, 30 minutes on Thurday, 45 minutes on Wednesday and Friday, and 12 hours on Sunday. I will also be able to come on Monday for 14 hours."
}
```
