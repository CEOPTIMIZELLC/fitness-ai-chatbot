_availability_request = {
    "description": """**Availability** — Changes to their weekly or daily availability (e.g., new days or times they can train).""", 
    "ex_output": """- `availability`: is_requested = true, detail = "User is no longer available on Wednesdays." """}

_macrocycle_request = {
    "description": """**Macrocycle** — Updates to their long-term goals, such as focusing on muscle gain, fat loss, or sport performance over several months.""", 
    "ex_output": """- `macrocycle`: is_requested = false, detail = null """}

_mesocycle_request = {
    "description": """**Mesocycle** — Modifications to the training blocks or phases (e.g., shifting from strength to hypertrophy, changing phase durations).""", 
    "ex_output": """- `mesocycle`: is_requested = true, detail = "User wants to shift focus to hypertrophy for this mesocycle." """}

_microcycle_request = {
    "description": """**Microcycle** — Weekly routine structure (e.g., changing number of training days, spacing of workouts).""", 
    "ex_output": """- `microcycle`: is_requested = true, detail = "User wants to train 5 days per week." """}

_phase_component_request = {
    "description": """**Phase Components** — Specific requests about which types of workouts should be included in a single microcycle (e.g., more endurance, less strength).""", 
    "ex_output": """- `phase_component`: is_requested = false, detail = null """}

_workout_schedule_request = {
    "description": """**Workout Schedule** — Specific exercise-level requests within a workout (e.g., changing exercises, sets, reps, or focus).""", 
    "ex_output": """- `workout_schedule`: is_requested = true, detail = "Add core work to the upper body workout." """}

_workout_complete_request = {
    "description": """**Workout Complete** — Specifically indicates whether the user has completed their current workout. This should only be true if the user has SPECIFICALLY mentioned that they have completed their workout.""", 
    "ex_output": """- `workout_completion`: is_requested = false, detail = null """}

_goal_extraction_request = {
    "description": f"""1. {_availability_request["description"]}
2. {_macrocycle_request["description"]}
3. {_mesocycle_request["description"]}
4. {_microcycle_request["description"]}
5. {_phase_component_request["description"]}
6. {_workout_schedule_request["description"]}
7. {_workout_complete_request["description"]}""",
    "ex_output": f"""{_availability_request["ex_output"]}
{_macrocycle_request["ex_output"]}
{_mesocycle_request["ex_output"]}
{_microcycle_request["ex_output"]}
{_phase_component_request["ex_output"]}
{_workout_schedule_request["ex_output"]}
{_workout_complete_request["ex_output"]}"""
}

def retrieve_system_prompt(goal_request):
    return f"""
You are an expert on fitness and exercise routines, terminology, and understanding of the macro and micro scale of a workout routine.
You are extracting structured goal information from a user's input related to changes they want to make in their fitness routine. 
The routine is organized hierarchically from general to specific, and a user's message may indicate changes at one or multiple levels.

Please examine the user input and determine whether the user is requesting changes to each of the following levels:

{goal_request["description"]}

For each level, extract:
- A boolean field (`is_requested`) indicating whether the user's message expresses a desire to change that level.
- A string field (`detail`) that captures the relevant information or instruction the user gave about that level.

If no change is mentioned for a level, mark `is_requested` as `false` and leave the `detail` as `null`.

**Example Input:**
> "I want to start training 5 days a week now and focus more on hypertrophy this month. I also can't train on Wednesdays anymore. Can we add core to my upper body day too?"

**Corresponding Output:**
{goal_request["ex_output"]}

Return the result in the structured schema corresponding to the following Pydantic model: `RoutineImpactGoals`.

Be precise and extract only what the user explicitly or strongly implies.

If a user explicitly states they want to have a certain goal scheduled, the goal should be said to be requested.

The workout completion should only be said to be requested if it has EXPLICITLY been mentioned (e.g., 'I have completed my workout.')

"""


goal_extraction_system_prompt = retrieve_system_prompt(_goal_extraction_request)
availability_system_prompt = retrieve_system_prompt(_availability_request)
macrocycle_system_prompt = retrieve_system_prompt(_macrocycle_request)
mesocycle_system_prompt = retrieve_system_prompt(_mesocycle_request)
microcycle_system_prompt = retrieve_system_prompt(_microcycle_request)
phase_component_system_prompt = retrieve_system_prompt(_phase_component_request)
workout_schedule_system_prompt = retrieve_system_prompt(_workout_schedule_request)
workout_complete_system_prompt = retrieve_system_prompt(_workout_complete_request)