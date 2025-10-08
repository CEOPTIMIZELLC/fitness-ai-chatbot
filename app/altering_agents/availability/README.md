# Availability

## Description

The subagent involves the altering of the existing weekday availability for the user. The sub agent will parse the user's input and determine what changes need to be made to the availability for each weekday that is mentioned. This process includes initializing weekday entries for the user that don't currently exist in the database. Weekday's not specified will not be altered.

## Example Output

```
Checking classification of the following availability: User now has 30 minutes available every day.

Relevance determined: monday_availability=1800 tuesday_availability=1800 wednesday_availability=1800 thursday_availability=1800 friday_availability=1800 saturday_availability=1800 sunday_availability=1800

Availability Subagent: Retrieving the ID of the goal class.
Monday: 30 minutes and 0 seconds
Tuesday: 30 minutes and 0 seconds
Wednesday: 30 minutes and 0 seconds
Thursday: 30 minutes and 0 seconds
Friday: 30 minutes and 0 seconds
Saturday: 30 minutes and 0 seconds
Sunday: 30 minutes and 0 seconds

----------------------------------------
| No   | Weekday    | Availability
| 0    | Monday     | 30.0 minutes
| 1    | Tuesday    | 30.0 minutes
| 2    | Wednesday  | 30.0 minutes
| 3    | Thursday   | 30.0 minutes
| 4    | Friday     | 30.0 minutes
| 5    | Saturday   | 30.0 minutes
| 6    | Sunday     | 30.0 minutes
```