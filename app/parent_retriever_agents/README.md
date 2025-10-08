# Parent Retriever Agents

This folder holds the sub agents regarding and related to the retrieval and generation of parent items required for generating the current schedule item. 

## [Mesocycles/Phases](mesocycles/)

The subagent involves the retrieval of the parent schedule items (macrocycle) required to generate the mesocycles. The sub agent also requests the generation of the parent item and subsequent calling of the parent subagent if one doesn't exist.

## [Microcycles/Weekly Schedule](microcycles/)

The subagent involves the retrieval of the parent schedule items (mesoscyle) required to generate the microcycles. The sub agent also requests the generation of the parent item and subsequent calling of the parent subagent if one doesn't exist.

## [Phase Components for Each Week Day](phase_components/)

The subagent involves the retrieval of the parent schedule items (microcycle and availability) required to generate the phase components. The sub agent also requests the generation of the parent item and subsequent calling of the parent subagent if one doesn't exist.

## [Exercises/Daily Workouts](workout_schedule/)

The subagent involves the retrieval of the parent schedule items (phase component and availability) required to generate the exercises. The sub agent also requests the generation of the parent item and subsequent calling of the parent subagent if one doesn't exist.