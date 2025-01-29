# Dev Tests
Endpoints regarding the initialization of the database and data to be stored within.


## Retrieve Table Names
- Retrieves the names of all tables in the database.
```
[GET, POST] /dev_tests/retrieve_table_names
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


