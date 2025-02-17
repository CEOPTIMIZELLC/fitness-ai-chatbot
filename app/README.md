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

### [Dev Tests](dev_tests/)
- Restart database: `[GET, POST] /dev_tests/init_db`
