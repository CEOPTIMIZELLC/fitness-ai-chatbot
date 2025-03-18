from ortools.sat.python import cp_model
from typing_extensions import TypedDict
from datetime import datetime
from typing import Set, List, Optional
from dotenv import load_dotenv
from datetime import timedelta

from app.agents.constraints import create_optional_intvar, create_spread_intvar, day_duration_within_availability, use_workout_required_components, use_microcycle_required_components, frequency_within_min_max

#        \{\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*"phase_id": 5,\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n.*\n
phase_components_example = {
    "weekday_availability": [
        {"id": 0, "name": "Monday", "availability": 6 * 60 * 60},
        {"id": 1, "name": "Tuesday", "availability": 3 * 60 * 60},
        {"id": 2, "name": "Wednesday", "availability": 2 * 60 * 60},
        {"id": 3, "name": "Thursday", "availability": 35 * 60},
        {"id": 4, "name": "Friday", "availability": 0 * 60 * 60},
        {"id": 5, "name": "Saturday", "availability": 2 * 60 * 60},
        {"id": 6, "name": "Sunday", "availability": 0 * 60 * 60},
    ],
    "microcycle_weekdays": [0, 1, 2, 3, 4, 5, 6],
    "workout_length": 50 * 60,
    "phase_components": []
}

_ = load_dotenv()

class RelaxationAttempt:
    def __init__(self, constraints_relaxed: Set[str], result_feasible: bool, 
                 microcycle_duration: Optional[int] = None,
                 reasoning: Optional[str] = None, expected_impact: Optional[str] = None):
        self.constraints_relaxed = set(constraints_relaxed)
        self.result_feasible = result_feasible
        self.microcycle_duration = microcycle_duration
        self.timestamp = datetime.now()
        self.reasoning = reasoning
        self.expected_impact = expected_impact

class State(TypedDict):
    parameters: dict
    constraints: dict
    opt_model: any
    solution: any
    formatted: str
    output: list
    logs: str
    relaxation_attempts: list
    current_attempt: dict  # Include reasoning and impact
    parameter_input: dict

def setup_params_node(state: State, config=None) -> dict:

    parameter_input = state.get("parameter_input", {})
    
    """Initialize optimization parameters and constraints."""
    parameters = {
        "weekday_availability": phase_components_example["weekday_availability"],
        "microcycle_weekdays": phase_components_example["microcycle_weekdays"],
        "workout_length": phase_components_example["workout_length"],
        "phase_components": phase_components_example["phase_components"]        
    }

    # Define all constraints with their active status
    constraints = {
        "day_duration_within_availability": True,       # The time of a workout won't exceed the time allowed for that given day.
        "day_duration_within_workout_length": True,     # The time of a workout won't exceed the length allowed for a workout.
        "use_workout_required_components": True,        # Include phase components that are required in every workout at least once.
        "use_microcycle_required_components": True,     # Include phase components that are required in every microcycle at least once.
        "intensity_within_min_max": True,
        "frequency_within_min_max": True,               # The number of times that a phase component may be used in a microcycle is within number allowed.
        "exercises_per_bodypart_within_min_max": True,
        "minimize_duration_delta": False,               # Minimize the amount of spread across the duration of phase component over the microcycle.
        "minimize_sets_delta": True,                    # Minimize the amount of spread across the sets of phase component over the microcycle.
        "minimize_reps_delta": True,                    # Minimize the amount of spread across the reps of phase component over the microcycle.
        "minimize_bodypart_exercise_delta": True,       # Minimize the amount of spread across the number of exercises per phase component over the microcycle.
        "maximize_exercise_time": True,                 # Objective function constraint
    }

    # Merge in any new parameters or constraints from the provided config
    if "parameters" in parameter_input:
        parameters.update(parameter_input["parameters"])
    if "constraints" in parameter_input:
        constraints.update(parameter_input["constraints"])
    
    return {
        "parameters": parameters,
        "constraints": constraints,
        "opt_model": None,
        "solution": None,
        "formatted": "",
        "output": "",
        "logs": "Parameters and constraints initialized\n",
        "relaxation_attempts": [],
        "current_attempt": {
            "constraints": set(),
            "reasoning": None,
            "expected_impact": None
        }
    }


def declare_model_vars(model, microcycle_weekdays, weekday_availability, phase_components):
    workout_availability = []
    active_workday_vars = []
    active_phase_components = []
    seconds_per_exercise = []
    reps_vars = []
    sets_vars = []
    rest_vars = []
    bodypart_vars = []
    duration_vars = []

    # Each day in the microcycle
    for index_for_day, day in enumerate(microcycle_weekdays):
        workout_availability_for_day = weekday_availability[day]["availability"]
        is_active_workday = model.NewBoolVar(f'day_{index_for_day}_active')

        # Ensure that the workday is considered inactive if it is 0 hours long.
        if workout_availability_for_day > 0:
            model.Add(is_active_workday == True)
        else:
            model.Add(is_active_workday == False)

        # Append the available time for a day. Make sure to convert it from hours to seconds.
        workout_availability.append(workout_availability_for_day)
        active_workday_vars.append(is_active_workday)
        
        seconds_per_exercise_for_day = []
        active_phase_components_for_day = []
        reps_vars_for_day = []
        sets_vars_for_day = []
        rest_vars_for_day = []
        bodypart_vars_for_day = []
        duration_vars_for_day = []

        # Each phase component in the day.
        for index_for_phase_component, phase_component in enumerate(phase_components):
            is_phase_active_var = (model.NewBoolVar(
                f'phase_component_{index_for_phase_component}_active_on_day_{index_for_day}'))
            
            seconds_per_exercise_entry = phase_component["seconds_per_exercise"]

            # Create an optional entry for the reps variables.
            model, reps_var_entry = create_optional_intvar(
                model=model, activator=is_phase_active_var,
                min_if_active=phase_component["reps_min"],
                max_if_active=phase_component["reps_max"],
                name_of_entry_var=f'phase_component_{index_for_phase_component}_reps_on_day_{index_for_day}')

            # Create an optional entry for the sets variables.
            model, sets_var_entry = create_optional_intvar(
                model=model, activator=is_phase_active_var,
                min_if_active=phase_component["sets_min"],
                max_if_active=phase_component["sets_max"],
                name_of_entry_var=f'phase_component_{index_for_phase_component}_sets_on_day_{index_for_day}')

            # Create an optional entry for the rests variables.
            model, rest_var_entry = create_optional_intvar(
                model=model, activator=is_phase_active_var,
                min_if_active=phase_component["rest_min"] // 5,     # Adjusted so that rest is a multiple of 5.
                max_if_active=phase_component["rest_max"] // 5,     # Adjusted so that rest is a multiple of 5.
                name_of_entry_var=f'phase_component_{index_for_phase_component}_rest_on_day_{index_for_day}')

            # Create an optional entry for the bodyparts variables.
            model, bodypart_var_entry = create_optional_intvar(
                model=model, activator=is_phase_active_var,
                min_if_active=phase_component["exercises_per_bodypart_workout_min"] if phase_component["exercises_per_bodypart_workout_min"] else 1,
                max_if_active=phase_component["exercises_per_bodypart_workout_max"] if phase_component["exercises_per_bodypart_workout_max"] else 1,
                name_of_entry_var=f'phase_component_{index_for_phase_component}_exercises_per_bodypart_on_day_{index_for_day}')
            
            # Create the entry for phase component's duration
            # phase duration = number_of_bodypart_exercises * (seconds_per_exercise * rep_count + rest_time) * set_count
            duration_var_entry = model.NewIntVar(
                0, workout_availability_for_day, 
                f'phase_component_{index_for_phase_component}_duration_on_day_{index_for_day}')

            # Due to inability to make an expression as a constraint in a single line, a few steps must be taken prior.
            # Temporary variable for seconds per exercise and the rep count. (seconds_per_exercise * rep_count)
            seconds_per_exercise_and_reps = model.NewIntVar(
                0, workout_availability_for_day, 
                f'phase_component_{index_for_phase_component}_seconds_per_exercise_and_rep_count_on_day_{index_for_day}')
            
            model.AddMultiplicationEquality(seconds_per_exercise_and_reps, [seconds_per_exercise_entry, reps_var_entry])

            # Temporary variable for the previous product and the rest time. (seconds_per_exercise * rep_count + rest_time)
            duration_with_rest = model.NewIntVar(
                0, workout_availability_for_day, 
                f'phase_component_{index_for_phase_component}_duration_with_rest_on_day_{index_for_day}')
            
            # In between step for added components.
            model.Add(duration_with_rest == seconds_per_exercise_and_reps + (5 * rest_var_entry))

            # Completed constraint.
            model.AddMultiplicationEquality(duration_var_entry, [bodypart_var_entry, duration_with_rest, sets_var_entry])#.OnlyEnforceIf(is_phase_active_var)
            #model.Add(duration_var_entry == 0).OnlyEnforceIf(is_phase_active_var.Not())
            
            seconds_per_exercise_for_day.append(seconds_per_exercise_entry)
            active_phase_components_for_day.append(is_phase_active_var)
            reps_vars_for_day.append(reps_var_entry)
            sets_vars_for_day.append(sets_var_entry)
            rest_vars_for_day.append(rest_var_entry)
            bodypart_vars_for_day.append(bodypart_var_entry)
            duration_vars_for_day.append(duration_var_entry)
        
        # Append the new row to the corresponding 2D arrays.
        seconds_per_exercise.append(seconds_per_exercise_for_day)
        active_phase_components.append(active_phase_components_for_day)
        reps_vars.append(reps_vars_for_day)
        sets_vars.append(sets_vars_for_day)
        rest_vars.append(rest_vars_for_day)
        bodypart_vars.append(bodypart_vars_for_day)
        duration_vars.append(duration_vars_for_day)
    return (model, workout_availability, active_workday_vars, active_phase_components, 
            seconds_per_exercise, reps_vars, sets_vars, rest_vars, bodypart_vars, duration_vars)

def build_opt_model_node(state: State, config=None) -> dict:
    """Build the optimization model with active constraints."""
    parameters = state["parameters"]
    constraints = state["constraints"]
    model = cp_model.CpModel()

    phase_components = parameters["phase_components"]
    weekday_availability = parameters["weekday_availability"]
    workout_length = parameters["workout_length"]
    microcycle_weekdays = parameters["microcycle_weekdays"]

    (model, workout_availability, active_workday_vars, active_phase_components, seconds_per_exercise, 
     reps_vars, sets_vars, rest_vars, bodypart_vars, duration_vars) = declare_model_vars(model, microcycle_weekdays, weekday_availability, phase_components)

    # Apply active constraints ======================================
    state["logs"] += "\nBuilding model with constraints:\n"

    # Constraint: The duration of a day may only be a number of hours between the allowed time for that day.
    if constraints["day_duration_within_availability"]:
        model = day_duration_within_availability(model=model, 
                                             duration_vars=duration_vars, 
                                             availability=workout_availability)
        state["logs"] += "- Sum of phase component duration within maximum allowed time for a day.\n"

    # Ensure that the duration doesn't exceed the maximum allowed time for a workout.
    #model.Add(duration_var_entry <= workout_length)
    # Constraint: The duration of a day may only be a number of hours less than the allowed time for a workout.
    if constraints["day_duration_within_workout_length"]:
        model = day_duration_within_availability(model=model, 
                                             duration_vars=duration_vars, 
                                             availability=[workout_length] * len(duration_vars))
        state["logs"] += "- Sum of phase component duration within maximum allowed time for a workout.\n"


    # Constraint: Force all phase components required in every workout to be included at least once.
    if constraints["use_workout_required_components"]:
        # Retrieve the indexes of all components that are required in all workouts.
        required_phase_components = [i for i, phase_component in enumerate(phase_components) if phase_component["required_every_workout"]]
        model = use_workout_required_components(model=model, 
                                                required_phase_components=required_phase_components, 
                                                active_phase_components=active_phase_components, 
                                                active_workday_vars=active_workday_vars)
        state["logs"] += "- All phase components required every workout will be included in every workout applied.\n"

    # Constraint: Force all phase components required in every microcycle to be included at least once.
    if constraints["use_microcycle_required_components"]:
        # Retrieve the indexes of all components that are required at least once in a microcycle.
        required_phase_components = [i for i, phase_component in enumerate(phase_components) if phase_component["required_within_microcycle"] == "always"]
        model = use_microcycle_required_components(model=model, 
                                                   required_phase_components=required_phase_components, 
                                                   active_phase_components=active_phase_components)
        state["logs"] += "- All phase components required every microcycle will be included in every microcycle applied.\n"

    # Constraint: # Force number of occurrences of a phase component within in a microcycle to be within number allowed.
    if constraints["frequency_within_min_max"]:
        model = frequency_within_min_max(model=model, 
                                         phase_components=phase_components, 
                                         active_phase_components=active_phase_components)
        state["logs"] += "- All phase components occuring within microcycle will occur the allowed number of times applied.\n"
    
    duration_spread_var = None
    # Secondary Objective: Minimize the spread of duration.
    if constraints["minimize_duration_delta"]:
        model, duration_spread_var = create_spread_intvar(model=model, 
                                                          entry_vars=duration_vars, 
                                                          entry_var_name="duration_var", 
                                                          active_entry_vars=active_phase_components, 
                                                          max_value_allowed=max(workout_availability))
        state["logs"] += "- Minimizing spread across duration applied.\n"

    reps_spread_var = None
    # Secondary Objective: Minimize the spread of reps.
    if constraints["minimize_reps_delta"]:
        model, reps_spread_var = create_spread_intvar(model=model, 
                                                          entry_vars=reps_vars, 
                                                          entry_var_name="reps_var", 
                                                          active_entry_vars=active_phase_components, 
                                                          max_value_allowed=max(workout_availability))
        state["logs"] += "- Minimizing spread across reps applied.\n"

    sets_spread_var = None
    # Secondary Objective: Minimize the spread of sets.
    if constraints["minimize_sets_delta"]:
        model, sets_spread_var = create_spread_intvar(model=model, 
                                                          entry_vars=sets_vars, 
                                                          entry_var_name="sets_var", 
                                                          active_entry_vars=active_phase_components, 
                                                          max_value_allowed=max(workout_availability))
        state["logs"] += "- Minimizing spread across sets applied.\n"

    bodypart_spread_var = None
    # Secondary Objective: Minimize the spread of exercise numbers.
    if constraints["minimize_bodypart_exercise_delta"]:
        model, bodypart_spread_var = create_spread_intvar(model=model, 
                                                          entry_vars=bodypart_vars, 
                                                          entry_var_name="bodypart_var", 
                                                          active_entry_vars=active_phase_components, 
                                                          max_value_allowed=max(workout_availability))
        state["logs"] += "- Minimizing spread across exercise count applied.\n"



    # Objective: Maximize total duration of microcycle
    if constraints["maximize_exercise_time"]:
        # List of contributions to goal time.
        total_set_duration_for_day = []

        # Each day
        for duration_vars_for_day in duration_vars:
            # Each phase component
            for duration_vars_for_phase_component in duration_vars_for_day:
                total_set_duration_for_day.append(duration_vars_for_phase_component)
        
        # If minimizing the spread is a constraint, subtract it from the sum.
        total_duration_to_maximize = sum(total_set_duration_for_day)

        # Spread reduction.
        if duration_spread_var != None:
            total_duration_to_maximize -= duration_spread_var
        if bodypart_spread_var != None:
            total_duration_to_maximize -= bodypart_spread_var
        if reps_spread_var != None:
            total_duration_to_maximize -= reps_spread_var
        if sets_spread_var != None:
            total_duration_to_maximize -= sets_spread_var

        # Maximize the total
        model.Maximize(total_duration_to_maximize)
        state["logs"] += "- Maximizing time used in mesocycle.\n"

    return {"opt_model": (model, workout_availability, seconds_per_exercise, active_phase_components, reps_vars, sets_vars, rest_vars, bodypart_vars)}



def solve_model_node(state: State, config=None) -> dict:
    """Solve model and record relaxation attempt results."""
    model, workout_availability, seconds_per_exercise, active_phase_components, reps_vars, sets_vars, rest_vars, bodypart_vars = state["opt_model"]

    solver = cp_model.CpSolver()
    #solver.parameters.log_search_progress = True
    status = solver.Solve(model)
    
    state["logs"] += f"\nSolver status: {status}\n"
    state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"
    
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        microcycle_duration = 0
        schedule = []

        # Each day in the microcycle
        for index_for_day, values_for_day in enumerate(zip(workout_availability, seconds_per_exercise, active_phase_components, reps_vars, sets_vars, rest_vars, bodypart_vars)):
            (
                workout_availability_for_day, 
                seconds_per_exercise_for_day,
                active_phase_components_for_day, 
                reps_vars_for_day, 
                sets_vars_for_day, 
                rest_vars_for_day, 
                bodypart_vars_for_day
            ) = values_for_day

            # Each phase used in the day.
            for index_for_phase_component, values_for_phase_component in enumerate(zip(seconds_per_exercise_for_day, active_phase_components_for_day, reps_vars_for_day, sets_vars_for_day, rest_vars_for_day, bodypart_vars_for_day)):
                (
                    seconds_per_exercise_for_phase_component,
                    active_phase_components_for_phase_component, 
                    reps_vars_for_phase_component, 
                    sets_vars_for_phase_component, 
                    rest_vars_for_phase_component, 
                    bodypart_vars_for_phase_component
                ) = values_for_phase_component

                # Ensure that the phase component is active.
                if(solver.Value(active_phase_components_for_phase_component)):
                    seconds_per_exercise_current = solver.Value(seconds_per_exercise_for_phase_component)
                    reps_vars_current = solver.Value(reps_vars_for_phase_component)
                    sets_vars_current = solver.Value(sets_vars_for_phase_component)
                    rest_vars_current = 5 * solver.Value(rest_vars_for_phase_component)
                    bodypart_vars_current = solver.Value(bodypart_vars_for_phase_component)

                    schedule.append((
                        index_for_phase_component, index_for_day, 
                        seconds_per_exercise_current, 
                        solver.Value(active_phase_components_for_phase_component), 
                        reps_vars_current, 
                        sets_vars_current, 
                        rest_vars_current, 
                        bodypart_vars_current
                    ))
                    microcycle_duration += (bodypart_vars_current * (seconds_per_exercise_current * reps_vars_current + rest_vars_current) * sets_vars_current)
        solution = {
            "schedule": schedule,
            "microcycle_duration": microcycle_duration,
            "status": status
        }
        
        # Record successful attempt
        attempt = RelaxationAttempt(
            state["current_attempt"]["constraints"],
            True,
            microcycle_duration,
            state["current_attempt"]["reasoning"],
            state["current_attempt"]["expected_impact"]
        )
        state["relaxation_attempts"].append(attempt)
        return {"solution": solution}
    
    # Record unsuccessful attempt
    attempt = RelaxationAttempt(
        state["current_attempt"]["constraints"],
        False,
        None,
        state["current_attempt"]["reasoning"],
        state["current_attempt"]["expected_impact"]
    )
    state["relaxation_attempts"].append(attempt)
    return {"solution": None}

def format_solution_node(state: State, config=None) -> dict:
    """Format the optimization results."""
    solution = state["solution"]

    parameters = state["parameters"]

    phase_components = parameters["phase_components"]
    weekday_availability = parameters["weekday_availability"]
    workout_length = parameters["workout_length"]
    microcycle_weekdays = parameters["microcycle_weekdays"]

    longest_string_size = len(max(phase_components, key=lambda d:len(d["sub_component"]))["sub_component"])

    used_days = []
    
    # Total time the user has to workout.
    workout_time = 0
    for day in microcycle_weekdays:
        workout_availability = min(workout_length, weekday_availability[day]["availability"])
        used_days.append({"used": False, "availability": workout_availability})
        workout_time += workout_availability

    formatted = "Optimization Results:\n"
    formatted += "=" * 50 + "\n\n"
    
    # Show relaxation attempts history
    formatted += "Relaxation Attempts:\n"
    formatted += "-" * 40 + "\n"
    for i, attempt in enumerate(state["relaxation_attempts"], 1):
        formatted += f"\nAttempt {i}:\n"
        formatted += f"Constraints relaxed: {attempt.constraints_relaxed}\n"
        formatted += f"Result: {'Feasible' if attempt.result_feasible else 'Infeasible'}\n"
        if workout_time is not None:
            formatted += f"Total Hours Allowed: {workout_time  // 60} min {workout_time  % 60} sec ({workout_time} seconds)\n"
        if workout_length is not None:
            formatted += f"Workout Length Allowed: {workout_length  // 60} min {workout_length  % 60} sec ({workout_length} seconds)\n"
        if attempt.microcycle_duration is not None:
            formatted += f"Total Time Used: {attempt.microcycle_duration  // 60} min {attempt.microcycle_duration  % 60} sec ({attempt.microcycle_duration} seconds)\n"
        if attempt.reasoning:
            formatted += f"Reasoning: {attempt.reasoning}\n"
        if attempt.expected_impact:
            formatted += f"Expected Impact: {attempt.expected_impact}\n"
        formatted += f"Timestamp: {attempt.timestamp}\n"
    
    final_output = []
    phase_component_count = [0] * len(phase_components)

    if solution is None:
        formatted += "\nNo valid schedule found even with relaxed constraints.\n"
    else:
        
        schedule = solution["schedule"]
        
        formatted += "\nFinal Training Schedule:\n"
        formatted += "-" * 40 + "\n"
        
        for component_count, (phase_component_index, workday_index, 
                  seconds_per_exercise, active_phase_components, 
                  reps_var, sets_var, rest_var, bodypart_var) in enumerate(schedule):

            phase_component = phase_components[phase_component_index]
            phase_component_id = phase_component["id"]
            phase_component_name = phase_component["sub_component"]

            day_duration = (bodypart_var * (seconds_per_exercise * reps_var + rest_var) * sets_var)

            if active_phase_components:
                final_output.append({
                    "workday_index": workday_index, 
                    "phase_component_index": phase_component_index, 
                    "phase_component_id": phase_component_id,
                    "seconds_per_exercise": seconds_per_exercise, 
                    "active_phase_components": active_phase_components, 
                    "reps_var": reps_var, 
                    "sets_var": sets_var, 
                    "rest_var": rest_var, 
                    "bodypart_var": bodypart_var
                })

                current_weekday = microcycle_weekdays[workday_index]

                if not used_days[workday_index]["used"]:
                    formatted += f"\nDay {workday_index + 1} {weekday_availability[current_weekday]["name"]:<{10}} Availability of {used_days[workday_index]["availability"]  // 60} min {used_days[workday_index]["availability"]  % 60} sec ({used_days[workday_index]["availability"]} seconds)\n"
                    used_days[workday_index]["used"] = True

                # Count the number of occurrences of each phase component
                phase_component_count[phase_component_index] += 1

                formatted_duration = f"Duration: {day_duration  // 60} min {day_duration  % 60} sec ({day_duration} seconds)\t"

                formatted_seconds_per_exercises = f"Sec/Exercise {seconds_per_exercise:<{5}}"
                formatted_reps = f"Reps {reps_var} ({phase_component["reps_min"]:<{3}}-{phase_component["reps_max"]:<{3}})\t"
                formatted_sets = f"Sets {sets_var} ({phase_component["sets_min"]:<{2}}-{phase_component["sets_max"]:<{2}})\t"
                formatted_rest = f"Rest {rest_var} ({phase_component["rest_min"]}-{phase_component["rest_max"]})\t"
                formatted_bodyparts = f"Bodypart Exercises {bodypart_var} ({phase_component["exercises_per_bodypart_workout_min"]} - {phase_component["exercises_per_bodypart_workout_max"]})"

                formatted += (f"\tComp {(component_count + 1):<{3}}: {phase_component_name:<{longest_string_size+3}} ({formatted_duration} {formatted_seconds_per_exercises} {formatted_reps} {formatted_sets} {formatted_rest} {formatted_bodyparts})\n")
            else:
                formatted += (f"Day {workday_index + 1}; Comp {component_count + 1}: \t{phase_component_name:<{longest_string_size+3}} ----\n")

        formatted += f"Phase Component Counts:\n"
        for phase_component_index, phase_component_number in enumerate(phase_component_count):
            phase_component = phase_components[phase_component_index]
            formatted += f"\t{phase_component["sub_component"]:<{longest_string_size+3}}: {phase_component_number} ({phase_component["frequency_per_microcycle_min"]} - {phase_component["frequency_per_microcycle_max"]})\n"
        formatted += f"Total Time Used: {solution['microcycle_duration']  // 60} min {solution['microcycle_duration']  % 60} sec ({solution['microcycle_duration']}) seconds\n"
        formatted += f"Total Time Allowed: {workout_time  // 60} min {workout_time  % 60} sec ({workout_time} seconds)\n"
        formatted += f"Workout Length Allowed: {workout_length  // 60} min {workout_length  % 60} sec ({workout_length} seconds)\n"

        # Show final constraint status
        formatted += "\nFinal Constraint Status:\n"
        for constraint, active in state["constraints"].items():
            formatted += f"- {constraint}: {'Active' if active else 'Relaxed'}\n"
        
    
    return {"formatted": formatted, "output": final_output}

# Build the graph
from langgraph.graph import StateGraph, START, END

def create_optimization_graph():
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("setup", setup_params_node)
    builder.add_node("build", build_opt_model_node)
    builder.add_node("solve", solve_model_node)
    builder.add_node("format", format_solution_node)

    # Add edges
    builder.add_edge(START, "setup")
    builder.add_edge("setup", "build")
    builder.add_edge("build", "solve")
    builder.add_edge("solve", "format")
    builder.add_edge("format", END)

    return builder.compile()

def Main(parameter_input=None):
    # Create and run the graph
    graph = create_optimization_graph()
    
    initial_state = {
        "parameters": {},
        "constraints": {},
        "opt_model": None,
        "solution": None,
        "formatted": "",
        "output": "",
        "logs": "",
        "relaxation_attempts": [],
        "current_attempt": {"constraints": set(), "reasoning": None, "expected_impact": None}
    }

    # If parameter_input is provided, add them into the state
    if parameter_input is not None:
        initial_state["parameter_input"] = parameter_input

    result = graph.invoke(initial_state)
    return {"formatted": result["formatted"], "output": result["output"], "solution": result["solution"]}

if __name__ == "__main__":
    result = Main()
    print(result["formatted"])
