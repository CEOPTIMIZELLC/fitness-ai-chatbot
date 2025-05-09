# Fitness AI Chatbot Backend App
Application folder for the backend of the Fitness AI Chatbot. 

## List of Endpoints
All of the endpoints within the project are listed below. They are given and explained in more detail in the folders holding said routes.

All endpoints should begin with `localhost:5000`


### [Database Manipulation](routes/database_manipulation.py)
| Method | Route | Body | Description |
| --- | --- | --- | --- |
| **[GET, POST]** | `/database_manipulation/drop_db` | | Drops current database. |
| **[GET, POST]** | `/database_manipulation/create_db` | **(form-data)**: `email, password, password_confirm, first_name, last_name, age, gender, goal` | Create infrastructure and populate data for database. If all information is provided, it will also register a user. |
| **[GET, POST]** | `/database_manipulation/init_db` | **(form-data)**: `email, password, password_confirm, first_name, last_name, age, gender, goal` | Restarts database by calling the drop and create database functions. |
| **[GET, POST]** | `/database_manipulation/read_all_tables` | | Retrieves all information from all tables. |
| **[GET, POST]** | `/database_manipulation/read_table` | **(form-data)**: `table_name` | Retrieves all information from a given table. |

### [Dev Tests](routes/dev_tests.py)
| Method | Route | Body | Description |
| --- | --- | --- | --- |
| **[GET]** | `/dev_tests/pipeline` | | Retrieves the current state of the pipeline for the current user. |
| **[POST]** | `/dev_tests/pipeline` | **(raw)**: `availability, goal, runs (optional, default=1)` | Runs the pipeline for the current user, including the availability for each workday and the maximum workout length. |

### [Authentication](routes/auth.py)
Routes related to the creation and deletion of accounts and users, as well as logging in and logging out.
| Method | Route | Body | Description |
| --- | --- | --- | --- |
| **[GET, POST]** | `/register` | **(form-data)**: `email, password, password_confirm, first_name, last_name, age, gender, goal` | Register new user |
| **[POST]** | `/login` | **(form-data)**: `email, password` | Login user |
| **[POST]** | `/logout` | | Logout current user |
| **[DELETE]** | `/delete_account` | **(form-data)**: `password` | Delete current user |

### [User Info](routes/users.py)
| Method | Route | Body | Description |
| --- | --- | --- | --- |
| **[GET]** | `/current_user` | | List current user's information |
| **[PATCH]** | `/current_user` | **(raw)**: `first_name (optional), last_name (optional)` | Change current user's miscellaneous information |
| **[PATCH]** | `/current_user/change_email` | **(raw)**: `new_email, password` | Change current user's email |
| **[PATCH]** | `/current_user/change_password` | **(raw)**: `password, new_password, new_password_confirm` | Change current user's password |

### [User Weekday Availability](routes/user_weekday_availability.py)
| Method | Route | Body | Description |
| --- | --- | --- | --- |
| **[GET]** | `/user_weekday_availability` | | List current user's weekdays |
| **[POST, PATCH]** | `/user_weekday_availability` | **(raw)**: `availability` | Change current user's weekday availability by parsing the information from a user message. |

### [User Macrocycles](routes/user_macrocycles.py)
| Method | Route | Body | Description |
| --- | --- | --- | --- |
| **[GET]** | `/user_macrocycles` | | List current user's past and present macrocycles |
| **[GET]** | `/user_macrocycles/current` | | Retrieve current user's currently active macrocycle |
| **[POST]** | `/user_macrocycles` | **(raw)**: `goal` | Perform goal classification on a new goal to create a new macrocycle. |
| **[PATCH]** | `/user_macrocycles` | **(raw)**: `goal` | Perform goal classification for a new goal to alter the current macrocycle. |
| **[GET, POST]** | `/user_macrocycles/test` | | Perform unit test for goal classification for multiple example goals |

### [User Mesocycles](routes/user_mesocycles.py)
| Method | Route | Description |
| --- | --- | --- |
| **[GET]** | `/user_mesocycles` | List current user's past and present mesocycles |
| **[GET]** | `/user_mesocycles/current_list` | List current user's mesocycles for the currently active macrocycle |
| **[GET]** | `/user_mesocycles/current` | Retrieve current user's currently active mesocycle |
| **[POST, PATCH]** | `/user_mesocycles` | Perform phase classification for the current user's currently active macrocycle |
| **[GET, POST]** | `/user_mesocycles/test` | Perform unit test for phase classification for for every viable goal type |

### [User Microcycles](routes/user_microcycles.py)
| Method | Route | Description |
| --- | --- | --- |
| **[GET]** | `/user_microcycles` | List current user's past and present microcycles |
| **[GET]** | `/user_microcycles/current_list` | List current user's microcycles for the currently active mesocycle |
| **[GET]** | `/user_microcycles/current` | Retrieve current user's currently active microcycle |
| **[POST, PATCH]** | `/user_microcycles` | Creates a microcycle for every week in the current mesocycle |

### [User Workout Days](routes/user_workout_days.py)
| Method | Route |  Description |
| --- | --- | --- |
| **[GET]** | `/user_workout_days` | List current user's past and present work days along with each day's components |
| **[GET]** | `/user_workout_days/current_list` | List current user's work days (and corresponding components) for the currently active microcycle |
| **[GET]** | `/user_workout_days/current` | Retrieve current user's currently active work day (and corresponding components) |
| **[POST, PATCH]** | `/user_workout_days` | Perform phase component classification for the current user's currently active microcycle |
| **[GET, POST]** | `/user_workout_days/test` | Perform unit test for phase component classification for for every viable phase type for a mesocycle |

### [User Workout Exercises](routes/user_workout_exercises.py)
| Method | Route | Description |
| --- | --- | --- |
| **[GET]** | `/user_workout_exercises` | List current user's past and present workout exercises |
| **[GET]** | `/user_workout_exercises/current_list` | List current user's workout exercises for the currently active work day |
