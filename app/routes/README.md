# Authentication
The authentication endpoints handle the basic registration and user handling of the application.

## Register new user
- Adds new user to the users database. 
- Required inputs: `email`, `password`, `password_confirm`, `first_name`, `last_name`, `age`, `gender`, `goal`
- Returns status message on success or failure.
- Email address must be in a valid email format.
    - Returns information about incorrect formatting. ex: `Can only have one @.`
- Passwords must:
    - Be between 8 and 20 characters long.
    - Contain at least one number.
    - Have at least one of the following characters: `! @ # $ % ^ & * _ ?`
    - Returns error about what specifications were missed.
- Both passwords must match to confirm.
```
[GET, POST] /register
email
password
password_confirm (same as password to work)
first_name
last_name
age
gender
goal
```
## Login user
- Logs in user and stores the current user. 
- Required inputs: `email`, `password`
- Returns status message on success or failure. Doesn't work if already logged in.
- Routes that require user login to access re-route here if no current user.
- Requires user to be in the database.
```
[POST] /login
email
password
```
## Logout current user
- Logs out current user. 
- Only works if logged in.
```
[POST] /logout
```
## Delete current user
- Deletes the logged in user and logs them out.
- Required inputs: `password`
- Doing this deletes all inventory, customers, and orders attached to them.
- Requires input of user's password to confirm this.
```
[DELETE] /delete_account
password
```

# User Workout Information (Macrocycles, Mesocycles, Microcycles, Workout Days)
## List all that belong to user
For the selected information, retrieves all active and non active information.
```
[GET] /user_[macrocycle, mesocycle, microcycle, workout_days]/
```

## List all currently occurring
This retrieves the list of entries for the current higher level item. (i.e. all mesocycles for the current macrocycle, all microcycles for the current mesocycle)
```
[GET] /user_[macrocycle, mesocycle, microcycle, workout_days]/current_list
```

# Retrieve currently occurring entry
This retrieves whatever entry is currently ongoing. If multiple are, somehow, then this retrieves the lastest of the currently ongoing entries.
```
[GET] /user_[macrocycle, mesocycle, microcycle, workout_days]/current
```

## Perform Entry Decision Code
With this endpoint, it will generate the desired entries if able to (i.e. generating the mesocycles based on your current macrocycle.)
```
[POST, PATCH] /user_[macrocycle, mesocycle, microcycle, workout_days]/
```

## Perform Unit Test
With this endpoint, it will run through the generation for every higher level input (i.e. generating the mesocycles for every macrocycle). This doesn't save the information.
```
[GET, POST] /user_[macrocycle, mesocycle, microcycle, workout_days]/
```


# Current User Info
## List current user's information
- Retrieves the information on the currently logged in user.
- Returns user information as json.
```
[GET] /current-user
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


