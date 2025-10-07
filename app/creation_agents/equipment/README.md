# Equipment

## Description

The subagent involves the creation of a new piece of equipment for the user. 

The sub agent will ask in a loop for clarifying details until the user has provided it with enough information (the equipment type and the measurement) to create this new piece of equipment.

## Future Features

* Some pieces of equipment do not require a measurement.
* Some pieces of equipment will require multiple pieces of equipment.

## Example Output

```
Extract the goals from the following message: User would like to add a 24-pound barbell.
Parsed Goal Fields:
equipment_id: 18
equipment_measurement: 24

----------------------------------------
| Unique ID   | Equipment  | Measurement  | Unit of Measurement  
| 130         | Barbell    | 24           | None
```