# Reading Agents

This folder holds the main schedule sub agents that will control whether reading, altering, creation, or deletion will be performed. 

## [Equipment](user_equipment/)

The subagent controls the pipeline for deletion, creation, altering, and/or reading of the user's equipment.

## [Availability](user_weekdays_availability/)

The subagent controls the pipeline for altering and/or reading of the user's availability for each workday.

## [Macrocycles/Goals](user_macrocycles/)

The subagent controls the pipeline for creation, altering, and/or reading of the user's macrocycles/goals. `Future implementations will implement deletion of existing items.`

## [Mesocycles/Phases](user_mesocycles/)

The subagent controls the pipeline for creation and/or reading of the user's mesocycles/phases. `Future implementations will implement altering and/or deletion of existing items.`

## [Microcycles/Weekly Schedule](user_microcycles/)

The subagent controls the pipeline for creation and/or reading of the user's microcycles/weekly schedules. `Future implementations will implement altering and/or deletion of existing items.`

## [Phase Components for Each Week Day](user_workout_days/)

The subagent controls the pipeline for creation and/or reading of the user's phase components. `Future implementations will implement altering and/or deletion of existing items.`

## [Exercises/Daily Workouts](user_workout_exercises/)

The subagent controls the pipeline for creation and/or reading of the user's exercises/daily workouts. `Future implementations will implement altering and/or deletion of existing items.`

## [Daily Workout Completion](user_workout_completion/)

The subagent controls the pipeline for executing the scripts for the user's workout to be completed.