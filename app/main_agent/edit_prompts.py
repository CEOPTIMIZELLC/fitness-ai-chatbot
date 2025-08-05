_workout_complete_request = {
    "description": """**Workout** — Specifically indicates what changes that the user would like to make to their workout schedule to reflect the actual effort put in.""", 
    "ex_output": """- is_requested = true, detail = "The user has only been able to perform 3 sets for the pushups.", other_requests: "I want to start training 5 days a week now and focus more on hypertrophy this month. I also can't train on Wednesdays anymore. Can we add core to my upper body day too?" """}


def retrieve_system_prompt(goal_request):
    return f"""
You are an expert on fitness and exercise routines, terminology, and understanding of the macro and micro scale of a workout routine.
A user has previously been presented with a schedule and may request edits to the schedule.
You are extracting structured information from the user's input regarding if the user wants to make edits to the schedule, what edits they would like to make to the schedule, and any miscellaneous information from the 

Please examine the user input and determine whether the user is requesting changes to each of the following levels:

{goal_request["description"]}

For each level, extract:
- A boolean field (`is_requested`) indicating whether the user's message expresses a desire to alter the schedule.
- A string field (`detail`) that captures the relevant information or instruction the user gave about that level.

As well, some may have a
- A boolean field (`alter_old`) indicating whether the user's message expresses a desire to alter the currently existing element. This should only be true if it is explicitly mentioned.


If no change is mentioned for a level, mark `is_requested` as `false` and leave the `detail` as `null`.

**Example Input:**
> "I want to start training 5 days a week now and focus more on hypertrophy this month. I have only been able to perform 3 of the sets for the pushups. I also can't train on Wednesdays anymore. Can we add core to my upper body day too?"

**Corresponding Output:**
{goal_request["ex_output"]}

Return the result in the structured schema corresponding to the following Pydantic model: `EditGoal`.

Be precise and extract only what the user explicitly or strongly implies.

If a user explicitly states they want to have a certain goal scheduled, the goal should be said to be requested.

"""

workout_edit_system_prompt = retrieve_system_prompt(_workout_complete_request)