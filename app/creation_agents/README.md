# Creation Agents

This folder holds the sub agents regarding and related to the creation of new schedule items. 

## [Equipment](equipment/)

The subagent involves the creation of a new piece of equipment for the user. The sub agent will ask in a loop for clarifying details until the user has provided it with enough information (the equipment type and the measurement) to create this new piece of equipment. `Future implementations will not require the measurment when not needed (i.e. when a piece of equipment doesn't typically have a measurement). Future implementations will ideally have multiple measurements when necessary (i.e. when a piece of equipment has a length and a weight)/`

## [Macrocycles/Goals](macrocycles/)

The subagent involves the creation of a new active macrocycle. The sub agent will parse the user's input and determine what goal type it falls into. `Future implementations will allow the user to clarify when they want it to start, rather than having it start at the current date.`

## [Mesocycles/Phases](mesocycles/)

The subagent involves the creation of multiple mesocycles to fall within the currently active macrocycle, determining phase and length for each. `Future implementations will allow the user to create mesocycles for future macrocycles as well.`

## [Microcycles/Weekly Schedule](microcycles/)

The subagent involves the division of the currently active mesocycle into week long microcycles. `Future implementations will allow the user to create microcycles for future mesocycles as well.`

## [Phase Components for Each Week Day](phase_components/)

The subagent involves the assignment of what phase components are to be performed for the on each day of the currently active microcycle. This includes: what bodypart and the duration. `Future implementations will allow the user to create phase components for future microcycles as well.`

## [Exercises/Daily Workout](workout_schedule/)

The subagent involves the creation of a workout for the currently active weekday, determining phase and length for each. `Future implementations will allow the user to create workouts for future microcycles as well.`