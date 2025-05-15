# Models

## [Component Library](component_library.py)
The library of components that exist for phase components.
| id | name |
| --- | --- |
| 1 | "Flexibility" |
| 2 | "Core" |
| 3 | "Balance" |
| 4 | "Plyometric" |
| 5 | "SAQ" |
| 6 | "Resistance" |

## [Equipment Library](equipment_library.py)
The library of equipment available.
| id | name | unit_of_measurement |
| --- | --- | --- |
| 1 | "Foam Roller" | "kilograms" |
| 2 | "Plyo Box" | "kilograms" |
| 3 | "Dumbell" | "kilometers" |
| 4 | "Treadmill" | "centimeters" |


## [Exercise Library](exercise_library.py)
The library of exercises possible.
| id | name | base_strain | technical_difficulty | tags | sides | body_position | option_for_added_weight | proprioceptive_progressions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | "Quadrip MFR" | 2 | 2 | "MFR" | "Unilateral" | "prone" | None | None |
| 2 | "Hamstring MFR" | 2 | 2 | "MFR" | "Unilateral" | "seated" | None | None |
| 14 | "Cobra Stretch" | 1 | 1 | "Static Stretch" | "Bilateral" | "prone" | None | None |
| 23 | "Supine Biceps Femoris Active Stretch" | 2 | 2 | "active isolated stretch" | "Unilateral" | "supine" | None | None |

## [Exercise Component Phases](exercise_component_phases.py)
The join table for the component and subcomponent combination that are attached to an exercise.
| exercise_id | component_id | subcomponent_id |
| --- | --- | --- |
| 1 | 1 | 1 |
| 1 | 2 | 1 |
| 1 | 3 | 1 |
| 1 | 4 | 1 |
| 1 | 5 | 1 |
| 1 | 6 | 1 |
| 2 | 1 | 1 |

## [Exercise Equipment](exercise_equipment.py)
### Exercise Assistive Equipment
The join table for the assistive equipment required for an exercises.
| exercise_id | equipment_id | quantity | equipment_relationship |
| --- | --- | --- | --- |
| 1 | 1 | 1 | [null] |
| 2 | 1 | 1 | [or] |
| 2 | 2 | 3 | [or] |
| 3 | 1 | 2 | [and] |
| 3 | 2 | 1 | [and] |
### Exercise Marking Equipment
The join table for the marking equipment required for an exercises.
| exercise_id | equipment_id | quantity | equipment_relationship |
| --- | --- | --- | --- |
| 1 | 1 | 1 | [null] |
| 2 | 1 | 1 | [or] |
| 2 | 2 | 3 | [or] |
| 3 | 1 | 2 | [and] |
| 3 | 2 | 1 | [and] |
### Exercise Other Equipment
The join table for the other equipment required for an exercises.
| exercise_id | equipment_id | quantity | equipment_relationship |
| --- | --- | --- | --- |
| 1 | 1 | 1 | [null] |
| 2 | 1 | 1 | [or] |
| 2 | 2 | 3 | [or] |
| 3 | 1 | 2 | [and] |
| 3 | 2 | 1 | [and] |
### Exercise Supportive Equipment
The join table for the supportive equipment required for an exercises.
| exercise_id | equipment_id | quantity | equipment_relationship |
| --- | --- | --- | --- |
| 1 | 1 | 1 | [null] |
| 2 | 1 | 1 | [or] |
| 2 | 2 | 3 | [or] |
| 3 | 1 | 2 | [and] |
| 3 | 2 | 1 | [and] |
### Exercise Weighted Equipment
The join table for the weighted equipment required for an exercises.
| exercise_id | equipment_id | quantity | equipment_relationship |
| --- | --- | --- | --- |
| 1 | 1 | 1 | [null] |
| 2 | 1 | 1 | [or] |
| 2 | 2 | 3 | [or] |
| 3 | 1 | 2 | [and] |
| 3 | 2 | 1 | [and] |

## [Exercise Muscle Categories](exercise_muscle_categories.py)
### Exercise Bodyparts
The join table for the bodyparts that an exercise targets.
| exercise_id | bodypart_id |
| --- | --- |
| 1 | 1 |
| 2 | 1 |
| 2 | 2 |

### Exercise Body Regions
The join table for the body regions that an exercise targets.
| exercise_id | body_region_id |
| --- | --- |
| 1 | 1 |
| 2 | 1 |
| 2 | 2 |

### Exercise Muscle Groups
The join table for the muscle groups that an exercise targets.
| exercise_id | muscle_group_id |
| --- | --- |
| 1 | 1 |
| 2 | 1 |
| 2 | 2 |

### Exercise Muscles
The join table for the muscles that an exercise targets.
| exercise_id | muscle_id |
| --- | --- |
| 1 | 1 |
| 2 | 1 |
| 2 | 2 |

## [Goal Library](goal_library.py)
The library of goals that a macrocycle can be classified as.
| id | name |
| --- | --- |
| 1 | "Fat Loss Goal" |
| 2 | "Hypertrophy Goal" |
| 3 | "General Sports Performance Goal" |
| 4 | "Unique Goal" |


## [Goal Phase Requirements](goal_phase_requirements.py)
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

## [Muscle Categories](muscle_categories.py)
### Muscle Categories
The join table for the different muscle groups that exist.
| muscle_id | muscle_group_id | bodypart_id | body_region_id |
| --- | --- | --- | --- |
| 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 2 |
| 3 | 1 | 3 | 2 |
| 4 | 1 | 4 | 2 |
| 5 | 1 | 5 | 2 |

### Muscle Group Library
The library of muscle groups that exist.
| id | name |
| --- | --- |
| 1 | "Chest" |
| 2 | "Biceps" |
| 3 | "Triceps" |
| 4 | "Shoulders" |
| 5 | "Back" |
| 6 | "Core" |
| 7 | "Legs" |

### Muscle Library
The library of muscles that exist.
| id | name |
| --- | --- |
| 1 | "Pectoralis Major" |
| 2 | "Pectoralis Minor" |
| 3 | "Serratus Anterior" |
| 4 | "Latissimus Dorsi" |
| 5 | "Trapezius" |
| 6 | "Deltoid" |
| 7 | "Biceps Brachii" |

### Bodypart Library
The library of bodyparts that exist.
| id | name |
| --- | --- |
| 1 | "total body" |
| 2 | "chest" |
| 3 | "biceps" |
| 4 | "triceps" |
| 5 | "shoulders" |
| 6 | "back" |
| 7 | "core" |
| 8 | "legs" |

### Body Region Library
The library of body regions that exist.
| id | name |
| --- | --- |
| 1 | "total body" |
| 2 | "upper body" |
| 3 | "core" |
| 4 | "lower body" |

## [Phase Library](phase_library.py)
The library of phases that a mesocycle can be classified as.
| id | name | phase_duration_minimum_in_weeks | phase_duration_maximum_in_weeks |
| --- | --- | --- | --- |
| 1 | "Stabilization Endurance" | 4 weeks | 6 weeks |
| 2 | "Strength Endurance" | 4 weeks | 4 weeks |
| 3 | "Hypertrophy" | 4 weeks | 4 weeks |
| 4 | "Maximal Strength" | 4 weeks | 4 weeks |
| 5 | "Power" | 4 weeks | 4 weeks |

## [Phase Component Library](phase_component_library.py)
The library of phase components that exist.
| id | phase_id | component_id | subcomponent_id | name | reps_min | reps_max | sets_min | sets_max | tempo | seconds_per_exercise | intensity_min | intensity_max | rest_min | rest_max | required_every_workout | required_within_microcycle | frequency_per_microcycle_min | frequency_per_microcycle_max | exercises_per_bodypart_workout_min | exercises_per_bodypart_workout_max | exercise_selection_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 1 | "flexibility-stabilization" | 1 | 1 | 1 | 3 | "30 s hold" | 30 |  |  | 0 | 0 | true | "always" |  |  |  |  | "SMR and static" |
| 2 | 1 | 2 | 1 | "core-stabilization" | 12 | 20 | 1 | 4 | "Slow 4/2/1" | 7 |  |  | 20 | 90 | false | "always" | 2 | 4 | 1 | 4 |  |
| 3 | 1 | 3 | 1 | "balance-stabilization" | 12 | 20 | 1 | 3 | "Slow 4/2/1" | 7 |  |  | 20 | 90 | false | "always" | 2 | 4 | 1 | 4 | "for SL exercises half the reps" |
| 4 | 1 | 4 | 1 | "plyometric-stabilization" | 5 | 8 | 1 | 3 | "3-5 s hold on landing" | 5 |  |  | 20 | 90 | false | "after core and balance sufficient" | 2 | 4 | 0 | 2 |  |
| 5 | 1 | 5 | 1 | "SAQ-stabilization" | 2 | 3 | 1 | 2 | "Moderate" | 3 |  |  | 20 | 90 | false | "after core and balance sufficient" | 2 | 4 | 4 | 6 | "drills with limited horizontal inertia and unpredictability" |
| 6 | 1 | 6 | 1 | "resistance-stabilization" | 12 | 20 | 1 | 3 | "Slow 4/2/1" | 7 | 50 | 70 | 20 | 90 | false | "always" | 2 | 4 | 1 | 2 | "stabilization progression" |

## [Phase Component Bodyparts](phase_component_bodyparts.py)
The join table for the different bodyparts that exist for each phase component.
| id | phase_id | component_id | bodypart_id | required_within_microcycle |
| --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 1 | "always" |
| 2 | 1 | 2 | 1 | "always" |
| 3 | 1 | 3 | 1 | "always" |
| 4 | 1 | 4 | 1 | "after core and balance sufficient" |

## [Subcomponent Library](subcomponent_library.py)
The library of subcomponents that exist for phase components.
| id | name | density | volume | load | explanation |
| --- | --- | --- | --- | --- | --- |
| 1 | "Stabilization" | 2 | 1 | 3 | "increase volume then density then load" |
| 2 | "Strength" | 3 | 2 | 1 | "increase load then volume then density" |
| 3 | "Power" | 3 | 1 | 2 | "increase volume then load then density" |

## [User Equipment](user_equipment.py)
The join table for what equipment a user has and the measurement of this equipment.
| id | user_id | equipment_id | measurement |
| --- | --- | --- | --- |
| 1 | 1 | 1 | 10 |
| 2 | 1 | 3 | 45 |

## [User Exercises](user_exercises.py)
The join table for what exercises a user has and the one rep max of this exercise.
| id | user_id | exercise_id | one_rep_max |
| --- | --- | --- | --- |
| 1 | 1 | 1 | 10 |
| 2 | 1 | 2 | 10 |

## [User Macrocycles](user_macrocycles.py)
The table of macrocycles that a user has, along with what goal type it is and the start and end date of the macrocycle.
| id | user_id | goal_id | goal | start_date | end_date |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 3 | "I would like to be ready for the soccer championship." | 3/4/2025 | 9/2/2025 |
| 2 | 3 | 1 | "I would like to weigh 100 pounds." | 3/4/2025 | 9/2/2025 |

## [User Mesocycles](user_mesocycles.py)
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

## [User Microcycles](user_microcycles.py)
The table of microcycles that a user's mesocycle has, along with the start and end date of the microcycle.
| id | mesocycle_id | order | start_date | end_date |
| --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 3/4/2025 | 3/11/2025 |
| 2 | 1 | 2 | 3/11/2025 | 3/18/2025 |

## [User Workout Days](user_workout_days.py)
The table of workout days that a user's microcycle has, along with the start and end date of the microcycle.
| id | microcycle_id | weekday_id | order | date |
| --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 1 | 3/4/2025 |
| 2 | 1 | 2 | 2 | 3/5/2025 |

## [User Workout Components](user_workout_components.py)
The join table for the different phase components that exist for each workout day in the user's microcycle.
| id | workout_day_id | phase_component_id | bodypart_id | duration |
| --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 1 | 10 |
| 2 | 1 | 2 | 1 | 10 |

## [User Workout Exercises](user_workout_exercises.py)
The join table for the different exercises that exist for each workout component in the user's microcycle.
| id | workout_day_id | phase_component_id | exercise_id | reps | sets | intensity | rest | weight | duration | working_duration | volume | density | performance | strained_duration | strained_working_duration | strain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 1 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| 2 | 1 | 2 | 1 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| 3 | 1 | 2 | 2 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |


## [Users](users.py)
| id | email | password_hash | first_name | last_name | age | gender | goal | start_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | bestfrienddoggy@email.com | hashed_password | Amanda | Writer | 35 | "Female" | "I want to improve my upperbody strength." | 10/10/2010 |

- Emails are set by the `set_email` method to ensure that emails are in the proper format before adding/changing.
- Passwords are set by `set_password`, which requires the same password to be provided for confirmation, as well as ensuring passwords follow the proper format.
- Passwords are not stored directly, but rather have a hash generated for them. This hash can be compared against a string to make sure they match.
- The user table also has the user mixin implemented, allowing for user login and management. 

## [User Weekday Availability](user_weekday_availability.py)
The table of weekday availabilities that a user has.
| user_id | weekday_id | availability |
| --- | --- | --- |
| 1 | 1 | 10 |
| 1 | 2 | 30 |
| 1 | 3 | 15 |
| 1 | 4 | 0 |
| 1 | 5 | 0 |
| 1 | 6 | 30 |
| 1 | 7 | 10 |

## [Weekday Library](weekday_library.py)
| id | name |
| --- | --- |
| 1 | "Monday" |
| 2 | "Tuesday" |
| 3 | "Wednesday" |
| 4 | "Thursday" |
| 5 | "Friday" |
| 6 | "Saturday" |
| 7 | "Sunday" |

## [Injury Library](injury_library.py)
| id | name | severity_levels |
