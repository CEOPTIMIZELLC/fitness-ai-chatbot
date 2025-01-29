## Models
### Users
| id | email | password_hash | first_name | last_name | age | gender | goal |
| --- | --- | --- | --- |
| 12 | bestfrienddoggy@email.com | hashed_password | Amanda | Writer | 35 | "Female" | "I want to improve my upperbody strength." |

- Emails are set by the `set_email` method to ensure that emails are in the proper format before adding/changing.
- Passwords are set by `set_password`, which requires the same password to be provided for confirmation, as well as ensuring passwords follow the proper format.
- Passwords are not stored directly, but rather have a hash generated for them. This hash can be compared against a string to make sure they match.
- The user table also has the user mixin implemented, allowing for user login and management. 

### Exercise_Library
| id | name | movement_type | primary_muscle_group | tempo | tracking |

### Equipment_Library
| id | name | measure |

### Injury_Library
| id | name | severity_levels |
