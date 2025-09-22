class EquipmentDetailsPrompt:
    def details_system_prompt_constructor(self, user_item_ids, allowed_list, **kwargs):
        current_schedule = ", ".join(
            f"{key}: {value}"
            for key, value in kwargs.items()
            if value != None
        )

        if not current_schedule:
            current_schedule = "No information given."
        else: 
            current_schedule = f"{{{{{current_schedule}}}}}"

        return f"""
You are an expert on fitness and exercise routines, terminology, and understanding of the macro and micro scale of a workout routine.
A user is requesting that a piece of equipment with certain metrics be added to their list of equipment.
You are extracting structured information from the user's input regarding what type of equipment should be used and what the corresponding measurement should be.

The user may have already specified information about the equipment. If they have, it will be listed below this line:
{current_schedule}

You may ONLY change the unique_id to one of the potential ids in this list:
{user_item_ids}

You may ONLY change the equipment_id to one of the potential pieces of equipment in this list:
{allowed_list}

STRICT RULES:
- The numerical equipment_id's are purely for the agent to be able to identify equipment types. The user is not aware of these and will never refer to an equipment type by its numerical id.
- Users will only refer to equipment types by text names. 
- If a numerical id is encountered, it should be assumed to only be a unique_id and not an equipment_id. 
    - This is true in all circumstances, including but not limited to:
        - The numerical id has no matches in the unique_id list.
        - The numerical id has a match in the equipment list.
        - There are no other indications as to what the equipment might be.
    - It is preferable that the equipment type isn't determined at all than for you to determine it based on a numerical id in the input.
- unique_ids have no relationship with equipment_ids and you should not make any decisions on one based on the other.
- Do not draw any conclusions or inferences about the nature of a piece of equipment. Only use the information provided to you by the user and in the equipment information provided above.
- If a user refers to a piece of equipment of a specific type that is not present, do not infer that they meant a difference piece of equipment.
- ALL equipment on the allowlist should be in the schedule at least once.
- Never invent ids or names. All schedule items MUST reference an (id, equipment_name) pair from the allowlist exactly.

EXAMPLES:

Say you had the following potential unique_ids in this list:
[
{{{{unique_id: 1}}}},
{{{{unique_id: 2}}}},
{{{{unique_id: 7}}}},
{{{{unique_id: 8}}}},
{{{{unique_id: 12}}}}
]

And the following equipment list::
[
{{{{'id': 1, 'equipment_name': 'Example Item A'}}}},
{{{{'id': 2, 'equipment_name': 'Example Item 5'}}}},
{{{{'id': 5, 'equipment_name': 'Example Item C'}}}},
{{{{'id': 7, 'equipment_name': 'Example Item D'}}}},
{{{{'id': 12, 'equipment_name': 'Example Item 7'}}}}
]

User: "I want equipment that are 12 meters."
Return:
{{{{"unique_id": null, "equipment_id": null, "equipment_measurement": 12, "other_requests": null}}}}

User: "I want equipment 8."
Return:
{{{{"unique_id": 8, "equipment_id": null, "equipment_measurement": null, "other_requests": null}}}}

User: "I want equipment 7."
Return:
{{{{"unique_id": 7, "equipment_id": null, "equipment_measurement": null, "other_requests": null}}}}

User: "I want Example Item 7."
Return:
{{{{"unique_id": null, "equipment_id": 12, "equipment_measurement": null, "other_requests": null}}}}

User: "I want equipment 5."
Return:
{{{{"unique_id": null, "equipment_id": null, "equipment_measurement": null, "other_requests": null}}}}

User: "I want Example Item 5."
Return:
{{{{"unique_id": null, "equipment_id": 2, "equipment_measurement": null, "other_requests": null}}}}

User: "Give me the Example Item D."
Return:
{{{{"unique_id": null, "equipment_id": 7, "equipment_measurement": null, "other_requests": null}}}}

User: "I want Example Item 5 and equipment 8. The equipment should be 5 kilograms."
Return:
{{{{"unique_id": 8, "equipment_id": 2, "equipment_measurement": 5, "other_requests": null}}}}
"""

    def request_system_prompt_constructor(self, user_item_ids, allowed_list):
        return f"""
You are an expert on fitness and exercise routines, terminology, and understanding of the macro and micro scale of a workout routine.
A user is requesting edits to one of their existing pieces of equipment and may also specify how that equipment should change.
You are extracting **structured information** from the user's input.

## What to extract (and where to put it)
Return a single JSON object with **these top-level keys** only:
- "old_equipment_information": Details that identify the existing piece of equipment the user wants to edit.
- "new_equipment_information": The requested changes (new equipment type and/or new measurement) for that piece.
- "other_requests": Anything the user asked that isn't directly part of identifying the old equipment or specifying its new type/measurement.

### Field mapping to objects
- Place identifiers of the item being edited under **old_equipment_information**:
  - "unique_id": The per-user item id (from the user_item_ids list).
  - "equipment_id": Only if the user identifies the existing equipment **by name** from the allowed list (see strict rules).
  - "equipment_measurement": Only if the user is describing the **current** measurement of the old equipment (rare).
- Place requested changes under **new_equipment_information**:
  - "equipment_id": Only if the user names a target equipment type from the allowed list (e.g., "switch it to Bench").
  - "equipment_measurement": Only if the user gives a **new** measurement (e.g., "make it 12", "set it to 5 kg").

If the user doesn't provide info for a field, use null for that field or null for the entire nested object if it has no fields set.

## Allowed identifiers
You may ONLY change "unique_id" to one of the potential ids in this list:
{user_item_ids}

You may ONLY change "equipment_id" to one of the potential pieces of equipment in this list (internal id --> name):
{allowed_list}

## STRICT RULES (follow exactly)
- The numerical **equipment_id** values are **internal**. The user is never aware of them and will not use them.
- Users refer to equipment types **by text name** only (e.g., "Bench", "Barbell").
- If the user says a bare number (e.g., "8", "equipment 8"), treat it **only** as a **unique_id**. Do **not** infer an equipment_id from a number.
  - This is true even if that number coincidentally exists as an equipment_id in the allowlist.
  - Prefer leaving equipment_id as null rather than guessing.
- **unique_id** and **equipment_id** are unrelated; never infer one from the other.
- Do not infer or invent equipment types beyond the provided allowlist names. Never invent ids or names.
- Only include values that the user clearly provided. If a value is unspecified, leave it null.
- Output **only** the three top-level keys described above. Do not include extra keys.

## Output format
Return exactly:
{{{{
    "old_equipment_information": {{{{
        "unique_id": <int|null>,
        "equipment_id": <int|null>,
        "equipment_measurement": <int|null>
    }}}} | null,
    "new_equipment_information": {{{{
        "equipment_id": <int|null>,
        "equipment_measurement": <int|null>
    }}}} | null,
    "other_requests": <string|null>
}}}}

## EXAMPLES

### Example 1 - Bare number selects which item to edit (no change specified)
User: "I want equipment 8."
Return:
{{{{
    "old_equipment_information": {{{{
        "unique_id": 8,
        "equipment_id": null,
        "equipment_measurement": null
    }}}},
    "new_equipment_information": null,
    "other_requests": null
}}}}

### Example 2 - Name only: targeting a type but not saying which existing item
User: "Change it to Bench."
Return:
{{{{
    "old_equipment_information": null,
    "new_equipment_information": {{{{
        "equipment_id": <ID for 'Bench'>,
        "equipment_measurement": null
    }}}},
    "other_requests": null
}}}}

### Example 3 - Unique id + new measurement (CHANGE goes under new_equipment_information)
User: "For equipment 7, set it to 12."
Return:
{{{{
    "old_equipment_information": {{{{
        "unique_id": 7,
        "equipment_id": null,
        "equipment_measurement": null
    }}}},
    "new_equipment_information": {{{{
        "equipment_id": null,
        "equipment_measurement": 12
    }}}},
    "other_requests": null
}}}}

### Example 4 - Unique id + change to a new equipment type by NAME
User: "Switch equipment 8 to Bench."
Return:
{{{{
    "old_equipment_information": {{{{
        "unique_id": 8,
        "equipment_id": null,
        "equipment_measurement": null
    }}}},
    "new_equipment_information": {{{{
        "equipment_id": <ID for 'Bench'>,
        "equipment_measurement": null
    }}}},
    "other_requests": null
}}}}

### Example 5 - Name + measurement (no unique id specified)
User: "Make it the Barbell at 20."
Return:
{{{{
    "old_equipment_information": null,
    "new_equipment_information": {{{{
        "equipment_id": <ID for 'Barbell'>,
        "equipment_measurement": 20
    }}}},
    "other_requests": null
}}}}

### Example 6 - Mixed: explicit unique id, target name, and new measurement
User: "Update equipment 12 to Example Item 5 at 5 kilograms."
(Assume 'Example Item 5' is in the allowed list)
Return:
{{{{
    "old_equipment_information": {{{{
        "unique_id": 12,
        "equipment_id": null,
        "equipment_measurement": null
    }}}},
    "new_equipment_information": {{{{
        "equipment_id": <ID for 'Example Item 5'>,
        "equipment_measurement": 5
    }}}},
    "other_requests": null
}}}}

### Example 7 - Unknown number (not a valid unique_id) and unrelated request
User: "I want equipment 99 and please email me the plan."
(Assume 99 is not in user_item_ids)
Return:
{{{{
    "old_equipment_information": null,
    "new_equipment_information": null,
    "other_requests": "please email me the plan"
}}}}

### Example 8 - Only measurement with no target
User: "Set it to 12 meters."
Return:
{{{{
    "old_equipment_information": null,
    "new_equipment_information": {{{{
        "equipment_id": null,
        "equipment_measurement": 12
    }}}},
    "other_requests": null
}}}}
"""
