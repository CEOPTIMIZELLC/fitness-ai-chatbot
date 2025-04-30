# Authentication
The authentication endpoints handle the basic registration and user handling of the application.
> 
> ## Register new user
> - Adds new user to the users database. 
> - Body type: `form-data`
> - Required inputs: `email`, `password`, `password_confirm`, `first_name`, `last_name`, `age`, `gender`, `goal`
> - Returns status message on success or failure.
> - Email address must be in a valid email format.
>     - Returns information about incorrect formatting. ex: `Can only have one @.`
> - Passwords must:
>     - Be between 8 and 20 characters long.
>     - Contain at least one number.
>     - Have at least one of the following characters: `! @ # $ % ^ & * _ ?`
>     - Returns error about what specifications were missed.
> - Both passwords must match to confirm.
> ```
> [GET, POST] /register
> email
> password
> password_confirm (same as password to work)
> first_name
> last_name
> age
> gender
> goal
> ```
> ## Login user
> - Logs in user and stores the current user. 
> - Body type: `form-data`
> - Required inputs: `email`, `password`
> - Returns status message on success or failure. Doesn't work if already logged in.
> - Routes that require user login to access re-route here if no current user.
> - Requires user to be in the database.
> ```
> [POST] /login
> email
> password
> ```
> ## Logout current user
> - Logs out current user. 
> - Only works if logged in.
> ```
> [POST] /logout
> ```
> ## Delete current user
> - Deletes the logged in user and logs them out.
> - Body type: `form-data`
> - Required inputs: `password`
> - Doing this deletes all inventory, customers, and orders attached to them.
> - Requires input of user's password to confirm this.
> ```
> [DELETE] /delete_account
> password
> ```
***

# Database Manipulation
The database manipulation endpoints handle the creation and deletion of the database.
> 
> ## Drop database
> - Drops the current database. 
> ```
> [GET, POST] /drop_db
> ```
> ## Create database
> - Creates the database. 
> - If all information is provided, it will also register a user.
> - Body type: `form-data`
> - Required inputs if registering a user: `email`, `password`, `password_confirm`, `first_name`, `last_name`, `age`, `gender`, `goal`
> ```
> [GET, POST] /create_db
> email (optional)
> password (optional)
> password_confirm (optional, same as password to work)
> first_name (optional)
> last_name (optional)
> age (optional)
> gender (optional)
> goal (optional)
> ```
> 
> ## Restart database
> - Restarts the database by calling the drop and create database functions. 
> - Body type: `form-data`
> - Required inputs if registering a user: `email`, `password`, `password_confirm`, `first_name`, `last_name`, `age`, `gender`, `goal`
> ```
> [GET, POST] /init_db
> email (optional)
> password (optional)
> password_confirm (optional, same as password to work)
> first_name (optional)
> last_name (optional)
> age (optional)
> gender (optional)
> goal (optional)
> ```
> 
> ## Retrieve the names of all tables in the database. 
> ```
> [GET, POST] /retrieve_table_names
> ```
> 
> ## Retrieve the schema of the database. 
> ```
> [GET, POST] /retrieve_db_schema
> ```
> 
> ## Retrieve all information from all tables. 
> ```
> [GET, POST] /read_all_tables
> ```
> 
> ## Retrieve all information from a given table. 
> - Body type: `form-data`
> - Required inputs: `table_name`
> ```
> [GET, POST] /read_table
> table_name
> ```
***

# Dev Tests
The dev tests endpoints handle the testing of the application. 
> ## Retrieve Pipeline's Current State
> - Retrieves the current state of the pipeline for the current user. 
> ```
> [GET] /dev_tests/pipeline
> ```
> 
> ## Run Pipeline
> - Runs the pipeline for the current user, including the availability for each workday and the maximum workout length. 
> - Body type: `raw`
> - Required inputs: `workout_length`, `availability`, `goal`
> - Optional inputs: `runs` (default=1)
> ```
> [POST] /dev_tests/pipeline
> workout_length
> availability
> goal
> runs (optional, default=1)
> ```
***

# User Info
Multiple sets of endpoints exist to handle the changing of the user's information. 
## User Info
The User Info endpoints handle the changing of the user's information. 
> ### List current user's information
> - Retrieves the information on the currently logged in user.
> - Returns user information as json.
> ```
> [GET] /current_user
> ```
> 
> ### Change current user's miscellaneous information
> - Changes the first and last name of the user.
> - Body type: `raw`
> ```
> [PATCH] /current_user
> first_name (optional)
> last_name (optional)
> ```
> 
> ### Change current user's maximum workout length
> - Changes the maximum workout length for the user.
> - Body type: `raw`
> - Required inputs: `workout_length`
> ```
> [PATCH] /current_user/change_workout_length
> workout_length
> ```
> 
> ### Change current user's email
> - Changes the email of the user.
> - Body type: `raw`
> - Required inputs: `new_email`, `password`
> - Requires user to be logged in.
> ```
> [PATCH] /current_user/change_email
> new_email
> password
> ```
> 
> ### Change current user's password
> - Changes the password of the user.
> - Body type: `raw`
> - Required inputs: `password`, `new_password`, `new_password_confirm`
> - Requires user to be logged in.
> ```
> [PATCH] /current_user/change_password
> password
> new_password
> new_password_confirm (same as new_password to work)
> ```

## User Exercises
The User Exercises endpoints handle the changing of the user's exercise information. 
> 
> ### List current user's exercise information
> - Retrieves the information on the currently logged in user's exercises.
> - Returns user exercise information as json.
> ```
> [GET] /user_exercises
> ```
> 
> ### Get current user's exercise information for single exercise
> - Retrieves the information on the currently logged in user's exercise.
> - Returns user exercise information as json.
> ```
> [GET] /user_exercises/<exercise_id>
> ```
> 
> ### List current user's exercise information for current workouts
> - Retrieves the information on the currently logged in user's exercise for the current workout.
> - Returns user exercise information as json.
> ```
> [GET] /user_exercises/current
> ```
> 
> ### List All Possible Exercises for the Current User
> - Retrieves the information on the currently logged in user's possible exercises.
> - Returns user exercise information as json.
> ```
> [GET] /user_exercises/possible
> ```

## User Weekday Availability
The User Weekday Availability endpoints handle the changing of the user's weekday availability. 
> 
> ### List current user's availability for each weekday
> ```
> [GET] /user_weekday_availability
> ```
> 
> ### Change current user's weekday availability by parsing the information from a user message. 
> - Body type: `raw`
> - Required inputs: `availability`
> ```
> [POST, PATCH] /user_weekday_availability
> availability
> ```

***
# Workout Planning
Multiple sets of endpoints exist to handle the planning of the user's workouts. 

## User Macrocycles
The User Macrocycles endpoints handle the planning of the user's macrocycles. 
> 
> ### List current user's past and present macrocycles
> ```
> [GET] /user_macrocycles
> ```
> 
> ### Retrieve current user's currently active macrocycle
> ```
> [GET] /user_macrocycles/current
> ```
> 
> ### Perform goal classification for the current user
> - Perform goal classification on a new goal to create a new macrocycle. 
> - Body type: `raw`
> - Required inputs: `goal`
> ```
> [POST, PATCH] /user_macrocycles
> goal
> ```
> 
> ### Perform unit test for goal classification for multiple example goals
> ```
> [GET, POST] /user_macrocycles/test
> ```

## User Mesocycles
The User Mesocycles endpoints handle the planning of the user's mesocycles. 
> 
> ### List current user's past and present mesocycles
> ```
> [GET] /user_mesocycles
> ```
> 
> ### List current user's mesocycles for the currently active macrocycle
> ```
> [GET] /user_mesocycles/current_list
> ```
> 
> ### Retrieve current user's currently active mesocycle
> ```
> [GET] /user_mesocycles/current
> ```
> 
> ### Perform phase classification for the current user's currently active macrocycle
> ```
> [POST, PATCH] /user_mesocycles
> ```
> 
> ### Perform unit test for phase classification for for every viable goal type
> ```
> [GET, POST] /user_mesocycles/test
> ```

## User Microcycles
The User Microcycles endpoints handle the planning of the user's microcycles. 
> 
> ### List current user's past and present microcycles
> ```
> [GET] /user_microcycles
> ```
> 
> ### List current user's microcycles for the currently active mesocycle
> ```
> [GET] /user_microcycles/current_list
> ```
> 
> ### Retrieve current user's currently active microcycle
> ```
> [GET] /user_microcycles/current
> ```
> 
> ### Creates a microcycle for every week in the current mesocycle
> ```
> [POST, PATCH] /user_microcycles
> ```

## User Workout Days
The User Workout Days endpoints handle the planning of the user's workout days for every microcycle in the current mesocycle.
> 
> ### List current user's past and present work days along with each day's components
> ```
> [GET] /user_workout_days
> ```
> 
> ### List current user's work days (and corresponding components) for the currently active microcycle
> ```
> [GET] /user_workout_days/current_list
> ```
> 
> ### Retrieve current user's currently active work day (and corresponding components)
> ```
> [GET] /user_workout_days/current
> ```
> 
> ### Perform phase component classification for the current user's currently active microcycle
> ```
> [POST, PATCH] /user_workout_days
> ```
> 
> ### Perform unit test for phase component classification for for every viable phase type for a mesocycle
> ```
> [GET, POST] /user_workout_days/test
> ```

# User Workout Exercises
The User Workout Exercises endpoints handle the planning of the user's exercises for every workout day in the current microcycle. 
> 
> ### List current user's past and present workout exercises
> ```
> [GET] /user_workout_exercises
> ```
> 
> ### List current user's workout exercises for the currently active work day
> ```
> [GET] /user_workout_exercises/current_list
> ```
> 
> ### Perform exercise classification for the current user's currently active workout day
> ```
> [POST, PATCH] /user_workout_exercises
> ```
> 
> ### Complete Workout
> - Indicate that the workout has been completed. 
> - Updates the user's exercise information. 
> ```
> [POST, PATCH] /user_workout_exercises/complete_workout
> ```
> 
> ### Initialize and Complete Workout
> - Perform exercise classification for the current user's currently active workout day. 
> - Indicate that the workout has been completed. 
> - Updates the user's exercise information. 
> ```
> [POST, PATCH] /user_workout_exercises/initialize_and_complete
> ```





***

# Libraries
Multiple sets of endpoints exist to simply view data in the database. 

## Components
The Components endpoints handle the viewing of the different components that a phase component can have.
> 
> ### List all components
> ```
> [GET] /components
> ```
> 
> ### Show component based on id.
> ```
> [GET] /components/<component_id>
> ```


## Equipment
The Equipment endpoints handle the viewing of the different types of equipment that exist.
> 
> ### List all equipment
> ```
> [GET] /equipment
> ```
> 
> ### Show equipment based on id.
> ```
> [GET] /equipment/<equipment_id>
> ```

## Exercises
The Exercises endpoints handle the viewing of the different exercises that exist.
> 
> ### List all exercises
> ```
> [GET] /exercises
> ```
> 
> ### Show exercise based on id.
> ```
> [GET] /exercises/<exercise_id>
> ```

## Goals
The Goals endpoints handle the viewing of the different types of goals that a macrocycle can be classified as.
> 
> ### List all goals
> ```
> [GET] /goals
> ```
> 
> ### Show goal based on id.
> ```
> [GET] /goals/<goal_id>
> ```

## Phase Components
The Phase Components endpoints handle the viewing of the different types of phase components that can be assigned to an workout.
> 
> ### List all phase components
> ```
> [GET] /phase_components
> ```
> 
> ### Show phase component based on id.
> ```
> [GET] /phase_components/<phase_component_id>
> ```

## Phases
The Phases endpoints handle the viewing of the different types of phases that a mesocycle can be classified as.
> 
> ### List all phases
> ```
> [GET] /phases
> ```
> 
> ### Show phase based on id.
> ```
> [GET] /phases/<phase_id>
> ```

## Subcomponents
The Subcomponents endpoints handle the viewing of the different types of subcomponents that a phase component can have.
> 
> ### List all subcomponents
> ```
> [GET] /subcomponents
> ```
> 
> ### Show subcomponent based on id.
> ```
> [GET] /subcomponents/<subcomponent_id>
> ```








# User Workout Information (Macrocycles, Mesocycles, Microcycles, Workout Days)
## List all that belong to user
For the selected information, retrieves all active and non active information.
```
[GET] /user_[macrocycles, mesocycles, microcycles, workout_days]/
```

## List all currently occurring
This retrieves the list of entries for the current higher level item. (i.e. all mesocycles for the current macrocycles, all microcycles for the current mesocycle)
```
[GET] /user_[mesocycles, microcycles, workout_days]/current_list
```

# Retrieve currently occurring entry
This retrieves whatever entry is currently ongoing. If multiple are, somehow, then this retrieves the lastest of the currently ongoing entries.
```
[GET] /user_[macrocycles, mesocycles, microcycles, workout_days]/current
```

## Perform Entry Decision Code
With this endpoint, it will generate the desired entries if able to (i.e. generating the mesocycles based on your current macrocycle.)
```
[POST, PATCH] /user_[macrocycles, mesocycles, microcycles, workout_days]/
```

## Perform Unit Test
With this endpoint, it will run through the generation for every higher level input (i.e. generating the mesocycles for every macrocycle). This doesn't save the information.
```
[GET, POST] /user_[macrocycles, mesocycles, microcycles, workout_days]/
```


# Current User Info
## List current user's information
- Retrieves the information on the currently logged in user.
- Returns user information as json.
```
[GET] /current_user
```


# Dev Tests
Endpoints regarding the initialization of the database and data to be stored within.


## Retrieve Table Names
- Retrieves the names of all tables in the database.
```
[GET, POST] /dev_tests/retrieve_table_names
```

## Retrieve Table Schema
- Retrieves the schema of the database.
```
[GET, POST] /dev_tests/retrieve_db_schema
```

## Restart database
- Restarts the database and adds the following:
    - Four users **(to be implemented later)**
        - The fourth will be replaced by a user given one if all of the following are met: 
            -  `email`, `password`, `password_confirm`, `first_name`, `last_name`, `age`, `gender`, and `goal` are given.
            - Email address must be in a valid email format.
            - Passwords must:
                - Be between 8 and 20 characters long.
                - Contain at least one number.
                - Have at least one of the following characters: `! @ # $ % ^ & * _ ?`
            - Both passwords must match to confirm.
- **`WARNING: DELETES ALL PREVIOUS DATA!`**
```
[GET, POST] /dev_tests/init_db
(Entering a value for all of the following will add them to the database as the fourth user instead.)
email
password
password_confirm (same as password to work)
first_name
last_name
age
gender
goal
```


