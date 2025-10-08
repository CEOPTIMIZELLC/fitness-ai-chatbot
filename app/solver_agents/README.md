# Solver Agents

This folder holds the solver sub agents regarding and related to parsing of user inputs and the generation of schedules for the user. 

## [Availability](weekday_availability/)

The subagent involves the parsing of the user input to determine what days are changed and how much time the user has stated they have.

## [Macrocycles/Goals](goals/)

The subagent involves the parsing of the user input to determine what goal the user has for the macrocycle and classifying the type of goal that it falls into.

## [Mesocycles/Phases](phases/)

The subagent involves the using a linear solver to generate a schedule of phases for the macrocycle.

## [Phase Components for Each Week Day](phase_components/)

The subagent involves the using a linear solver to generate a schedule of phase components for the microcycle.

## [Exercises/Daily Workouts](exercises/)

The subagent involves the using a linear solver to generate a schedule of exercises for the phase component.