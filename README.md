# fitness-ai-chatbot
AI based personal trainer with ability to chat with clients to build and maintain personalized programs and daily workouts.

# Setup
Ensure that you have an environment file with the following environment variables filled out.

```bash
POSTRGRES_HOST=
POSTRGRES_DATABASE="fitness_db"
POSTRGRES_USER=
POSTRGRES_PASSWORD=

LANGUAGE_MODEL="gpt-4o-mini"
OPENAI_API_KEY=
```

If significant changes have been made to the models, it may be necessary to run the following from the parent directory to restart the database. As of right now, if you remove models that map to tables that would have foreign keys that rely on it, the code may not be able to drop them from the database with the current restarting route in the application. To get around this, a script has been created that will simply delete the old database and make a new empty one that can be used. 
```bash
poetry run python del_db.py
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
localhost:5000/auth/logout
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

Body (form-data):
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
localhost:5000/auth/login

Body (form-data):
email: [string; REQUIRED; Must be a valid email address that exists in the database]
password: [string; REQUIRED; Must be the same as the password that was used to register the user with the given email address.]
```

**Set Availability for Each Weekday**
```
[POST]
localhost:5000/user_weekday_availability/

Body (raw) [JSON]:
{
    "availability": "[string; REQUIRED; Message to send to the AI to extract your availability for each weekday.]"
}
```

**Set Workout Length**
```
[POST]
localhost:5000/current_user/change_workout_length

Body (raw) [JSON]:
{
    "workout_length": "[string; REQUIRED; Message to send to the AI to extract your maximum workout length.]"
}
```

**Set Current Goal/Create New Macrocycle**
```
[POST]
localhost:5000/user_macrocycles/

Body (raw) [JSON]:
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
localhost:5000/auth/logout
```

**Initialize Database with User (If you want to reset the database)**
```
[POST]
localhost:5000/database_manipulation/init_db

Body (form-data):
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
localhost:5000/auth/login

Body (form-data):
email: [string; REQUIRED; Must be a valid email address that exists in the database]
password: [string; REQUIRED; Must be the same as the password that was used to register the user with the given email address.]
```

**Run Pipeline**
```
[POST]
localhost:5000/dev_tests/pipeline

Body (raw) [JSON]:
{
    "availability": "[string; REQUIRED; Message to send to the AI to extract your availability for each weekday.]",
    "workout_length": "[string; REQUIRED; Message to send to the AI to extract your maximum workout length.]",
    "goal": "[string; REQUIRED; Message to send to the AI to extract your current goal and determine its type.]"
}
```


# Example Fields
## Example Run
**Logout User (If logged in)**
```
[POST]
localhost:5000/auth/logout
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

Body (form-data):
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
localhost:5000/auth/login

Body (form-data):
email: email2@gmail.com
password: password?2
```

**Set Availability for Each Weekday**
```
[POST]
localhost:5000/user_weekday_availability/

Body (raw) [JSON]:
{
    "availability": "I will be available for 35 minutes on Tuesday, 30 minutes on Thurday, 45 minutes on Wednesday and Friday, and 12 hours on Sunday. I will also be able to come on Monday for 14 hours."
}
```

**Set Workout Length**
```
[POST]
localhost:5000/current_user/change_workout_length

Body (raw) [JSON]:
{
    "workout_length": "I will be available for 30 minutes on Tuesday."
}
```

**Set Current Goal/Create New Macrocycle**
```
[POST]
localhost:5000/user_macrocycles/

Body (raw) [JSON]:
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
localhost:5000/auth/logout
```

**Initialize Database with User (If you want to reset the database)**
```
[POST]
localhost:5000/database_manipulation/init_db

Body (form-data):
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
localhost:5000/auth/login

Body (form-data):
email: email2@gmail.com
password: password?2
```

**Run Pipeline**
```
[POST]
localhost:5000/dev_tests/pipeline

Body (raw) [JSON]:
{
    "workout_length": "I will be available for 30 minutes on Tuesday.",
    "goal": "I would like to prepare for my soccer tournament.",
    "availability": "I will be available for 35 minutes on Tuesday, 30 minutes on Thurday, 45 minutes on Wednesday and Friday, and 12 hours on Sunday. I will also be able to come on Monday for 14 hours."
}
```
