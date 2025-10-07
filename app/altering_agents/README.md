# Altering Agents

This folder holds the sub agents regarding and related to the altering of existing schedule items. 

## [Equipment](equipment/)

The subagent involves the altering of a single piece of equipment for the user. The sub agent will ask in a loop for clarifying details until the user has provided it with enough information to only have one piece of equipment. `Future implementations will allow the user to say that they want to alter all of the pieces of equipment listed.`


## [Availability](availability/)

The subagent involves the altering of the existing weekday availability for the user. The sub agent will parse the user's input and determine what changes need to be made to the availability for each weekday that is mentioned. This process includes initializing weekday entries for the user that don't currently exist in the database. Weekday's not specified will not be altered.

## [Macrocycles/Goals](macrocycles/)

The subagent involves the altering of the currently active macrocycle. The sub agent will parse the user's input and determine what goal type it falls into. `Future implementations will allow the user to instruct the agent on which Macrocycle they want to alter, rather than only allowing them to alter the current one.`