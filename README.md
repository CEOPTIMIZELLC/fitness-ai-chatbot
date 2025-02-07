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

# Routes
## Dev Tests
| route | request type | required request form fields |
| - | - | - |
| dev_tests/test_equipment_sql | 'GET' | |
| dev_tests/retrieve_table_names | 'GET','POST' | |
| dev_tests/retrieve_db_schema | 'GET','POST' | |
| dev_tests/init_db | 'GET','POST' | email, password, password_confirm, first_name, last_name, age, gender, goal |
| dev_tests/read_table | 'GET' | table_name |
| dev_tests/test_equipment_sql | 'GET' | |

## Authentication Routes
| route | request type | required request form fields |
| - | - | - |
| auth/register | 'POST' | email, password, password_confirm, first_name, last_name, age, gender, goal |
| auth/login | 'POST' | email, password |
| auth/logout | 'GET', 'POST' | |
| auth/delete_account | 'DELETE' | password |
