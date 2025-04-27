## Models

### Equipment_Library
The library of equipment available.
| id | name | unit_of_measurement |
| --- | --- | --- |
| 1 | "barbell" | "kilograms" |
| 2 | "dumbbell" | "kilograms" |
| 3 | "treadmill" | "centimeters" |

### Exercise_Equipment
The join table for the equipment required for an exercises.
| exercise_id | equipment_id |
| --- | --- |
| 1 | 1 |
| 2 | 1 |
| 2 | 2 |

### Exercise_Library
The library of exercises possible.
| id | name | movement_type | primary_muscle_group | tempo | tracking |
| --- | --- | --- | --- | --- | --- |
| 1 | "bench press" | "compound" | "chest" | "3-1-2" | '{"reps": 10, "time": 30, "weight": 50}' |
| 2 | "bicep curl" | "isolation" | "biceps" | "3-0-1-0" | '{"reps": 10, "time": 30, "weight": 50}' |
| 3 | "jogging" | "isolation" | "legs" | "3-0-1-0" | '{"reps": 10, "time": 30, "weight": 50}' |

### Goal_Phase_Requirements
The join table for how required a phase is for a goal type.
| goal_id | phase_id | required_phase | is_goal_phase |
| --- | --- | --- | --- |
| 1 | 1 | "required" | True |
| 1 | 2 | "required" | True |
| 1 | 3 | "optional" | False |
| 1 | 4 | "unlikely" | False |
| 1 | 5 | "unlikely" | False |
| 2 | 1 | "required" | False |
| 2 | 2 | "required" | False |
| 2 | 3 | "required" | True |
| 2 | 4 | "required" | False |
| 2 | 5 | "unlikely" | False |
| 3 | 1 | "required" | False |
| 3 | 2 | "required" | False |
| 3 | 4 | "required" | False |
| 3 | 5 | "required" | True |

### Goal_Library
The library of goals that a macrocycle can be classified as.
| id | name |
| --- | --- |
| 1 | "Fat Loss Goal" |
| 2 | "Hypertrophy Goal" |
| 3 | "General Sports Performance Goal" |
| 4 | "Unique Goal" |

### Phase_Library
The library of phases that a mesocycle can be classified as.
| id | name | phase_duration_minimum_in_weeks | phase_duration_maximum_in_weeks |
| --- | --- | --- | --- |
| 1 | "Stabilization Endurance" | 4 weeks | 6 weeks |
| 2 | "Strength Endurance" | 4 weeks | 4 weeks |
| 3 | "Hypertrophy" | 4 weeks | 4 weeks |
| 4 | "Maximal Strength" | 4 weeks | 4 weeks |
| 5 | "Power" | 4 weeks | 4 weeks |


### User_Equipment
The join table for what equipment a user has and the measurement of this equipment.
| id | user_id | equipment_id | measurement |
| --- | --- | --- | --- |
| 1 | 1 | 1 | 10 |
| 2 | 1 | 3 | 45 |

### User_Macrocycles
The table of macrocycles that a user has, along with what goal type it is and the start and end date of the macrocycle.
| id | user_id | goal_id | goal | start_date | end_date |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 3 | "I would like to be ready for the soccer championship." | 3/4/2025 | 9/2/2025 |
| 2 | 3 | 1 | "I would like to weigh 100 pounds." | 3/4/2025 | 9/2/2025 |

### User_Mesocycles
The table of mesocycles that a user's macrocycle has, along with what phase type it is and the start and end date of the macrocycle.
| id | macrocycle_id | phase_id | order | start_date | end_date |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 1 | 3/4/2025 | 4/1/2025 |
| 2 | 1 | 2 | 2 | 4/1/2025 | 4/29/2025 |
| 3 | 1 | 5 | 3 | 4/29/2025 | 5/27/2025 |
| 4 | 1 | 4 | 4 | 5/27/2025 | 6/24/2025 |
| 5 | 1 | 2 | 5 | 6/24/2025 | 7/22/2025 |
| 6 | 1 | 5 | 6 | 7/22/2025 | 8/19/2025 |
| 7 | 2 | 1 | 1 | 3/4/2025 | 4/1/2025 |
| 8 | 2 | 2 | 2 | 4/1/2025 | 4/29/2025 |
| 9 | 2 | 1 | 3 | 4/29/2025 | 5/27/2025 |
| 10 | 2 | 2 | 4 | 5/27/2025 | 6/24/2025 |
| 11 | 2 | 1 | 5 | 6/24/2025 | 7/22/2025 |
| 12 | 2 | 2 | 6 | 7/22/2025 | 8/19/2025 |

### Users
| id | email | password_hash | first_name | last_name | age | gender | goal | start_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | bestfrienddoggy@email.com | hashed_password | Amanda | Writer | 35 | "Female" | "I want to improve my upperbody strength." | 10/10/2010 |

- Emails are set by the `set_email` method to ensure that emails are in the proper format before adding/changing.
- Passwords are set by `set_password`, which requires the same password to be provided for confirmation, as well as ensuring passwords follow the proper format.
- Passwords are not stored directly, but rather have a hash generated for them. This hash can be compared against a string to make sure they match.
- The user table also has the user mixin implemented, allowing for user login and management. 



### Injury_Library
| id | name | severity_levels |
