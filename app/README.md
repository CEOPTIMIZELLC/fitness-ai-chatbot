# Fitness AI Chatbot Backend App
Application folder for the backend of the Fitness AI Chatbot. 

## Models
### Users
| id | email | password_hash | first_name | last_name | age | gender | goal |
| --- | --- | --- | --- |
| 12 | bestfrienddoggy@email.com | hashed_password | Amanda | Writer | 35 | "Female" | "I want to improve my upperbody strength." |

- Emails are set by the `set_email` method to ensure that emails are in the proper format before adding/changing.
- Passwords are set by `set_password`, which requires the same password to be provided for confirmation, as well as ensuring passwords follow the proper format.
- Passwords are not stored directly, but rather have a hash generated for them. This hash can be compared against a string to make sure they match.
- The user table also has the user mixin implemented, allowing for user login and management. 

## List of Endpoints
All of the endpoints within the project are listed below. They are given and explained in more detail in the folders holding said routes.

### [Authentication](auth/)
Routes related to the creation and deletion of accounts and users, as well as logging in and logging out.
- Register new user: `[GET, POST] /register`
- Login user: `[POST] /login`
- Logout current user: `[POST] /logout`
- Delete current user: `[DELETE] /delete_account`

### [User Info](users/)
- List current user's information: `[GET] /users`
- List current user's information: `[GET] /current-user`
- Change current user's email: `[GET, PATCH] /users/change_email`
- Change current user's password: `[GET, PATCH] /users/change_password`

### [User Macrocycles](user_macrocycles/)
- List current user's past and present macrocycles: `[GET] /user_macrocycles`
- Retrieve current user's currently active macrocycle: `[GET] /user_macrocycles/current`
- Perform goal classification for the current user: `[POST, PATCH] /user_macrocycles`
- Perform unit test for goal classification for multiple example goals: `[GET, POST] /user_macrocycles/test`

### [User Mesocycles](user_mesocycles/)
- List current user's past and present mesocycles: `[GET] /user_mesocycles`
- List current user's mesocycles for the currently active macrocycle: `[GET] /user_mesocycles/current_list`
- Retrieve current user's currently active mesocycle: `[GET] /user_mesocycles/current`
- Perform phase classification for the current user's currently active macrocycle: `[POST, PATCH] /user_mesocycles`
- Perform unit test for phase classification for for every viable goal type: `[GET, POST] /user_mesocycles/test`

### [User Microcycles](user_microcycles/)
- List current user's past and present microcycles: `[GET] /user_microcycles`
- List current user's microcycles for the currently active mesocycle: `[GET] /user_microcycles/current_list`
- Retrieve current user's currently active microcycle: `[GET] /user_microcycles/current`
- Creates a microcycle for every week in the current mesocycle: `[POST, PATCH] /user_microcycles`

### [User Workout Days](user_workout_days/)
- List current user's past and present work days along with each day's components: `[GET] /user_workout_days`
- List current user's work days (and corresponding components) for the currently active microcycle: `[GET] /user_workout_days/current_list`
- Retrieve current user's currently active work day (and corresponding components): `[GET] /user_workout_days/current`
- Perform phase component classification for the current user's currently active microcycle: `[POST, PATCH] /user_workout_days`
- Perform unit test for phase component classification for for every viable phase type for a mesocycle: `[GET, POST] /user_workout_days/test`

### [User Info](users/)
- List current user's information: `[GET] /users`
- List current user's information: `[GET] /current-user`
- Change current user's email: `[GET, PATCH] /users/change_email`
- Change current user's password: `[GET, PATCH] /users/change_password`

### [Dev Tests](dev_tests/)
- Restart database: `[GET, POST] /dev_tests/init_db`



# User Workout Information (Macrocycles, Mesocycles, Microcycles, Workout Days)
## List all that belong to user
For the selected information, retrieves all active and non active information.
```
user_macrocycles, user_mesocycles, user_microcycles, user_workout_days
```

## List all currently occurring
This retrieves the list of entries for the current higher level item. (i.e. all mesocycles for the current macrocycles, all microcycles for the current mesocycle)
```
[GET] /user_[macrocycles, mesocycles, microcycles, workout_days]/current_list
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
[GET] /current-user
```

