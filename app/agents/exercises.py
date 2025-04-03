from ortools.sat.python import cp_model
from typing_extensions import TypedDict
from datetime import datetime
from typing import Set, List, Optional
from dotenv import load_dotenv
from datetime import timedelta
import math

from app.agents.agent_helpers import retrieve_relaxation_history, analyze_infeasibility
from app.agents.constraints import entries_within_min_max, link_entry_and_item, constrain_active_entries_vars, create_optional_intvar, exercises_per_bodypart_within_min_max, create_duration_var, use_all_required_items, only_use_required_items
from app.agents.base_agent import BaseAgent, BaseAgentState

_ = load_dotenv()

class RelaxationAttempt:
    def __init__(self, constraints_relaxed: Set[str], result_feasible: bool, 
                 strain_ratio: Optional[int] = None,
                 duration: Optional[int] = None,
                 working_duration: Optional[int] = None,
                 reasoning: Optional[str] = None, expected_impact: Optional[str] = None):
        self.constraints_relaxed = set(constraints_relaxed)
        self.result_feasible = result_feasible
        self.strain_ratio = strain_ratio
        self.duration = duration
        self.working_duration = working_duration
        self.timestamp = datetime.now()
        self.reasoning = reasoning
        self.expected_impact = expected_impact

class State(BaseAgentState):
    parameter_input: dict

class ExerciseAgent(BaseAgent):
    def __init__(self, parameters={}, constraints={}):
        super().__init__()
        self.initial_state["parameter_input"]={
            "parameters": parameters, 
            "constraints": constraints}
    
    def setup_params_node(self, state: State, config=None) -> dict:
        """Initialize optimization parameters and constraints."""

        parameter_input = state.get("parameter_input", {})

        parameters = {
            "availability": 0,
            "workout_length": 0,
            "projected_duration": 0,
            "phase_components": [],
            "possible_exercises": []
        }

        # Define all constraints with their active status
        constraints = {
            "duration_within_availability": True,           # The time of a workout won't exceed the time allowed for that given day.
            "duration_within_workout_length": True,         # The time of a workout won't exceed the length allowed for a workout.
            "use_allowed_exercises": True,                  # Only use exercises that are allowed for the phase component and bodypart combination.
            "use_all_phase_components": True,               # At least one exercise should be given each phase component.
            "base_strain_within_min_max": True,             # The amount of base strain of the exercise may only be a number of weeks between the minimum and maximum base strain allowed for the exercise.
            "secs_within_min_max": True,                    # The number of seconds per exercise of the exercise may only be a number of weeks between the minimum and maximum seconds allowed for the phase component.
            "reps_within_min_max": True,                    # The number of reps of the exercise may only be a number of weeks between the minimum and maximum reps allowed for the phase component.
            "sets_within_min_max": True,                    # The number of sets of the exercise may only be a number of weeks between the minimum and maximum sets allowed for the phase component.
            "rest_within_min_max": True,                    # The number of rest of the exercise may only be a number of weeks between the minimum and maximum rest allowed for the phase component.
            "exercises_per_bodypart_within_min_max": True,  # The number of exercises for the phase components of the exercise may only be a number of weeks between the minimum and maximum exercises per bodypart allowed for the phase component.
            "minimize_strain": True,                        # Objective function constraint
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

    def build_opt_model_node(self, state: State, config=None) -> dict:
        """Build the optimization model with active constraints."""
        parameters = state["parameters"]
        constraints = state["constraints"]
        model = cp_model.CpModel()

        exercises = parameters["possible_exercises"]
        exercise_amount = len(exercises)

        phase_components = parameters["phase_components"]
        phase_component_amount = len(phase_components)

        projected_duration = parameters["projected_duration"]

        # Maximum amount of time that the workout may last
        workout_length = min(parameters["availability"], parameters["workout_length"])

        # Define variables =====================================

        # Upper bound on number of exercises (greedy estimation)
        min_exercises = sum((phase_component["exercises_per_bodypart_workout_min"] or 1) for phase_component in phase_components[1:])
        max_exercises = sum((phase_component["exercises_per_bodypart_workout_max"] or 1) for phase_component in phase_components[1:])
        min_seconds_per_exercise = min(phase_component["seconds_per_exercise"] for phase_component in phase_components[1:])
        max_seconds_per_exercise = max(phase_component["seconds_per_exercise"] for phase_component in phase_components[1:])
        min_reps = min(phase_component["reps_min"] for phase_component in phase_components[1:])
        max_reps = max(phase_component["reps_max"] for phase_component in phase_components[1:])
        min_sets = min(phase_component["sets_min"] for phase_component in phase_components[1:])
        max_sets = max(phase_component["sets_max"] for phase_component in phase_components[1:])
        min_rest = min(phase_component["rest_min"] for phase_component in phase_components[1:])
        max_rest = max(phase_component["rest_max"] for phase_component in phase_components[1:])
        min_base_strain = min(exercise["base_strain"] for exercise in exercises[1:])
        max_base_strain = max(exercise["base_strain"] for exercise in exercises[1:])

        used_exercise_vars = []
        used_pc_vars = []
        active_exercise_vars = []
        seconds_per_exercise_vars = []
        reps_vars = []
        sets_vars = []
        rest_vars = []
        phase_component_vars = []
        base_strain_vars = []
        exercise_vars = []
        duration_vars = []

        for i in range(max_exercises):
            # Boolean variables indicating whether exercise i is active.
            is_exercise_active_var = model.NewBoolVar(f'exercise_{i}_is_active')

            # Optional integer variable representing the exercise chosen at exercise i.
            model, exercise_var_entry = create_optional_intvar(
                model=model, activator=is_exercise_active_var,
                value_if_inactive=0,
                min_if_active=1,
                max_if_active=exercise_amount - 1,
                name_of_entry_var=f'exercise_{i}')

            # Boolean variables indicating whether exercise j is used at exercise i.
            used_exercise_vars_entry = [
                model.NewBoolVar(f'exercise_{i}_is_exercise_{j}')
                for j in range(exercise_amount)
            ]

            # Optional integer variable representing the phase component chosen at exercise i.
            model, phase_component_var_entry = create_optional_intvar(
                model=model, activator=is_exercise_active_var,
                value_if_inactive=0,
                min_if_active=1,
                max_if_active=phase_component_amount - 1,
                name_of_entry_var=f'phase_component_{i}')

            # Boolean variables indicating whether phase component j is used at exercise i.
            used_pc_vars_entry = [
                model.NewBoolVar(f'exercise_{i}_is_phase_component_{j}')
                for j in range(phase_component_amount)
            ]

            # Create an optional entry for the seconds per exercise variables.
            model, base_strain_var_entry = create_optional_intvar(
                model=model, activator=is_exercise_active_var,
                min_if_active=min_base_strain,
                max_if_active=max_base_strain,
                name_of_entry_var=f'base_strain_{i}')

            # Create an optional entry for the seconds per exercise variables.
            model, seconds_per_exercise_var_entry = create_optional_intvar(
                model=model, activator=is_exercise_active_var,
                min_if_active=min_seconds_per_exercise,
                max_if_active=max_seconds_per_exercise,
                name_of_entry_var=f'seconds_per_exercise_{i}')

            # Create an optional entry for the reps variables.
            model, reps_var_entry = create_optional_intvar(
                model=model, activator=is_exercise_active_var,
                min_if_active=min_reps,
                max_if_active=max_reps,
                name_of_entry_var=f'reps_{i}')

            # Create an optional entry for the sets variables.
            model, sets_var_entry = create_optional_intvar(
                model=model, activator=is_exercise_active_var,
                min_if_active=min_sets,
                max_if_active=max_sets,
                name_of_entry_var=f'sets_{i}')

            # Create an optional entry for the rests variables.
            model, rest_var_entry = create_optional_intvar(
                model=model, activator=is_exercise_active_var,
                min_if_active=min_rest,
                max_if_active=max_rest,
                name_of_entry_var=f'rest_{i}')

            model, duration_var_entry = create_duration_var(model=model, 
                                                    i=i, 
                                                    workout_length=workout_length, 
                                                    seconds_per_exercise=seconds_per_exercise_var_entry, 
                                                    reps=reps_var_entry, 
                                                    rest=rest_var_entry, 
                                                    sets=sets_var_entry)

            active_exercise_vars.append(is_exercise_active_var)
            used_exercise_vars.append(used_exercise_vars_entry)
            used_pc_vars.append(used_pc_vars_entry)
            base_strain_vars.append(base_strain_var_entry)
            seconds_per_exercise_vars.append(seconds_per_exercise_var_entry)
            reps_vars.append(reps_var_entry)
            sets_vars.append(sets_var_entry)
            rest_vars.append(rest_var_entry)
            phase_component_vars.append(phase_component_var_entry)
            exercise_vars.append(exercise_var_entry)
            duration_vars.append(duration_var_entry)

        # Introduce dynamic selection variables
        num_exercises_used = model.NewIntVar(min_exercises, max_exercises, 'num_exercises_used')
        model.Add(num_exercises_used == sum(active_exercise_vars))

        model = link_entry_and_item(model = model, 
                                    items = exercises, 
                                    entry_vars = exercise_vars, 
                                    number_of_entries = max_exercises, 
                                    used_vars = used_exercise_vars)

        model = link_entry_and_item(model = model, 
                                    items = phase_components, 
                                    entry_vars = phase_component_vars, 
                                    number_of_entries = max_exercises, 
                                    used_vars = used_pc_vars)
        
        model = constrain_active_entries_vars(model = model, 
                                            entry_vars = phase_component_vars, 
                                            number_of_entries = max_exercises, 
                                            duration_vars = duration_vars, 
                                            active_entry_vars = active_exercise_vars)

        # Apply active constraints ======================================
        state["logs"] += "\nBuilding model with constraints:\n"

        # Ensure total time is within two minutes of the originally calculated duration.
        model.Add(sum(duration_vars) <= workout_length)
        model.Add(sum(duration_vars) >= (projected_duration - (2 * 60)))

        # Constraint: Use only allowed exercises
        if constraints["use_allowed_exercises"]:
            for phase_component_index, phase_component in enumerate(phase_components[1:]):
                exercises_for_pc = [
                    i for i, exercise in enumerate(exercises[1:], start=1)
                    if (
                        exercise['component_id']==phase_component["component_id"] 
                        and exercise['subcomponent_id']==phase_component["subcomponent_id"]
                        #and exercise['bodypart_id']==phase_component["bodypart_id"]
                    )
                ]
            state["logs"] += "- Only use allowed exercises applied.\n"

        # Constraint: Use all required phases at least once
        if constraints["use_all_phase_components"]:
            required_phase_components = list(range(1, len(phase_components)))
            
            model = use_all_required_items(model = model, 
                                        required_items = required_phase_components, 
                                        entry_vars = phase_component_vars, 
                                        number_of_entries = max_exercises)
            state["logs"] += "- Use every required phase at least once applied.\n"

        # Constraint: The base strain of an exercise may only be between the minimum and maximum base strain allowed.
        if constraints["base_strain_within_min_max"]:
            model = entries_within_min_max(model = model, 
                                        items = exercises, 
                                        minimum_key="base_strain", 
                                        maximum_key="base_strain",
                                        number_of_entries = max_exercises, 
                                        used_vars = used_exercise_vars, 
                                        duration_vars = base_strain_vars)
            state["logs"] += "- Seconds per exercise count within min and max allowed seconds per exercise applied.\n"

        # Constraint: The seconds per exercise of a phase component may only be between the minimum and maximum seconds per exercise allowed.
        if constraints["secs_within_min_max"]:
            model = entries_within_min_max(model = model, 
                                        items = phase_components, 
                                        minimum_key="seconds_per_exercise", 
                                        maximum_key="seconds_per_exercise",
                                        number_of_entries = max_exercises, 
                                        used_vars = used_pc_vars, 
                                        duration_vars = seconds_per_exercise_vars)
            state["logs"] += "- Seconds per exercise count within min and max allowed seconds per exercise applied.\n"

        # Constraint: The reps of a phase component may only be a number of reps between the minimum and maximum reps allowed.
        if constraints["reps_within_min_max"]:
            model = entries_within_min_max(model = model, 
                                        items = phase_components, 
                                        minimum_key="reps_min", 
                                        maximum_key="reps_max",
                                        number_of_entries = max_exercises, 
                                        used_vars = used_pc_vars, 
                                        duration_vars = reps_vars)
            state["logs"] += "- Reps count within min and max allowed reps applied.\n"

        # Constraint: The sets of a phase component may only be a number of sets between the minimum and maximum sets allowed.
        if constraints["sets_within_min_max"]:
            model = entries_within_min_max(model = model, 
                                        items = phase_components, 
                                        minimum_key="sets_min", 
                                        maximum_key="sets_max",
                                        number_of_entries = max_exercises, 
                                        used_vars = used_pc_vars, 
                                        duration_vars = sets_vars)
            state["logs"] += "- Sets count within min and max allowed sets applied.\n"

        # Constraint: The rest of a phase component may only be a number of rest between the minimum and maximum rest allowed.
        if constraints["rest_within_min_max"]:
            model = entries_within_min_max(model = model, 
                                        items = phase_components, 
                                        minimum_key="rest_min", 
                                        maximum_key="rest_max",
                                        number_of_entries = max_exercises, 
                                        used_vars = used_pc_vars, 
                                        duration_vars = rest_vars)
            state["logs"] += "- Rest count within min and max allowed rest applied.\n"

        # Constraint: The numer of exercises may only be a number of exercises between the minimum and maximum exercises per bodypart allowed.
        if constraints["exercises_per_bodypart_within_min_max"]:
            model = exercises_per_bodypart_within_min_max(model=model, 
                                                        items=phase_components, 
                                                        minimum_key="exercises_per_bodypart_workout_min", 
                                                        maximum_key="exercises_per_bodypart_workout_max", 
                                                        used_vars=used_pc_vars)
            state["logs"] += "- Exercises count within min and max allowed exercises applied.\n"

        # Constraint: The duration of a day may only be a number of hours between the allowed time for that day.
        if constraints["duration_within_availability"]:
            state["logs"] += "- Sum of phase component duration within maximum allowed time for a day.\n"

        # Ensure that the duration doesn't exceed the maximum allowed time for a workout.
        #model.Add(duration_var_entry <= workout_length)
        # Constraint: The duration of a day may only be a number of hours less than the allowed time for a workout.
        if constraints["duration_within_workout_length"]:
            state["logs"] += "- Sum of phase component duration within maximum allowed time for a workout.\n"

        # Objective: Maximize total duration of microcycle
        if constraints["minimize_strain"]:
            # List of contributions to goal time.
            strain_terms = []

            # Creates strain_time, which will hold the total strain over the workout.
            strain_time = model.NewIntVar(0, max_exercises * workout_length, 'strain_time')
            for i, values_for_exercise in enumerate(zip(active_exercise_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars)):
                (
                    active_exercise_var, 
                    base_strain_var,
                    seconds_per_exercise_var, 
                    reps_var, 
                    sets_var, 
                    rest_var,
                    duration_var
                ) = values_for_exercise
                # Create the entry for phase component's duration
                # total_working_duration = (seconds_per_exercise*(1+.1*basestrain)* rep_count) * set_count
                working_duration_var = model.NewIntVar(0, workout_length, f'working_duration_{i}')
                non_zero_working_duration_var = model.NewIntVar(1, workout_length, f'working_duration_{i}')
                working_duration_is_0 = model.NewBoolVar(f'working_duration_{i}_is_0')

                model.AddMultiplicationEquality(working_duration_var, [seconds_per_exercise_var, reps_var, sets_var])

                # Ensure no division by 0 occurs.
                model.Add(non_zero_working_duration_var == 1).OnlyEnforceIf(working_duration_is_0)
                model.Add(non_zero_working_duration_var == working_duration_var).OnlyEnforceIf(working_duration_is_0.Not())
                model.Add(working_duration_var == 0).OnlyEnforceIf(working_duration_is_0)
                model.Add(working_duration_var > 0).OnlyEnforceIf(working_duration_is_0.Not())
                model.Add(working_duration_var == 0).OnlyEnforceIf(working_duration_is_0)
                model.Add(working_duration_var >= 1).OnlyEnforceIf(working_duration_is_0.Not())

                strain = model.NewIntVar(0, workout_length, f'strain_{i}')
                model.AddDivisionEquality(strain, duration_var, non_zero_working_duration_var)

                strain_terms.append(strain)

            model.Add(strain_time == sum(strain_terms))
            model.Minimize(strain_time)

            state["logs"] += "- Maximizing time used in workout.\n"

        return {"opt_model": (model, workout_length, exercise_vars, phase_component_vars, active_exercise_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars)}

    def analyze_infeasibility_node(self, state: State, config=None) -> dict:
        """Use LLM to analyze solver logs and suggest constraints to relax."""
        # Prepare history of what's been tried
        history = retrieve_relaxation_history(state["relaxation_attempts"])

        available_constraints = """
    - use_all_phase_components: Forces all phase components to be assigned at least once in a workout.
    - base_strain_within_min_max: Forces the amount of base strain to be between the minimum and maximum values allowed for the exercise.
    - use_allowed_exercises: Forces the exercise to be one of the exercises allowed for the phase component and bodypart combination.
    - secs_within_min_max: Forces the number of seconds per exercise to be between the minimum and maximum values allowed for the phase component.
    - reps_within_min_max: Forces the number of reps to be between the minimum and maximum values allowed for the phase component.
    - sets_within_min_max: Forces the number of sets to be between the minimum and maximum values allowed for the phase component.
    - rest_within_min_max: Forces the amount of rest to be between the minimum and maximum values allowed for the phase component.
    - exercises_per_bodypart_within_min_max: Forces the number of exercises for a phase component to be between the minimum and maximum values allowed.
    - minimize_strain: Objective to minimize the amount of strain overall.
    """

        state = analyze_infeasibility(state, history, available_constraints)
        
        return {
            "constraints": state["constraints"],
            "current_attempt": state["current_attempt"]
        }


    def solve_model_node(self, state: State, config=None) -> dict:
        """Solve model and record relaxation attempt results."""
        #return {"solution": "None"}
        model, workout_length, exercise_vars, phase_component_vars, active_exercise_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars = state["opt_model"]

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 24
        solver.parameters.log_search_progress = False
        status = solver.Solve(model)
        
        state["logs"] += f"\nSolver status: {status}\n"
        state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            strain_ratio = 0
            duration = 0
            working_duration = 0
            schedule = []
            # Each day in the microcycle
            for i, values_for_exercise in enumerate(zip(exercise_vars, phase_component_vars, active_exercise_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars)):
                (
                    exercise_var,
                    phase_component_var, 
                    active_exercise_var, 
                    base_strain_var,
                    seconds_per_exercise_var, 
                    reps_var, 
                    sets_var, 
                    rest_var,
                    duration_var
                ) = values_for_exercise

                # Ensure that the phase component is active.
                if(solver.Value(active_exercise_var)):
                    exercise_vars_current = solver.Value(exercise_var)
                    phase_component_vars_current = solver.Value(phase_component_var)
                    base_strain_vars_current = solver.Value(base_strain_var)
                    seconds_per_exercise_current = solver.Value(seconds_per_exercise_var)
                    reps_vars_current = solver.Value(reps_var)
                    sets_vars_current = solver.Value(sets_var)
                    rest_vars_current = solver.Value(rest_var) * 5
                    duration_vars_current = solver.Value(duration_var)
                    working_duration_vars_current = (seconds_per_exercise_current * reps_vars_current * sets_vars_current)
                    schedule.append((
                        i, exercise_vars_current, phase_component_vars_current, 
                        solver.Value(active_exercise_var), 
                        base_strain_vars_current, 
                        seconds_per_exercise_current, 
                        reps_vars_current, 
                        sets_vars_current, 
                        rest_vars_current, 
                        duration_vars_current,
                        working_duration_vars_current
                    ))
                    duration += duration_vars_current
                    working_duration += working_duration_vars_current
                    strain_ratio += duration_vars_current/working_duration_vars_current
            solution = {
                "schedule": schedule,
                "duration": duration,
                "working_duration": working_duration,
                "strain_ratio": strain_ratio,
                "status": status
            }
            
            # Record successful attempt
            attempt = RelaxationAttempt(
                state["current_attempt"]["constraints"],
                True,
                strain_ratio,
                duration,
                working_duration,
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
            None,
            None,
            state["current_attempt"]["reasoning"],
            state["current_attempt"]["expected_impact"]
        )
        state["relaxation_attempts"].append(attempt)
        return {"solution": None}

    def format_solution_node(self, state: State, config=None) -> dict:
        """Format the optimization results."""
        solution = state["solution"]

        parameters = state["parameters"]

        exercises = parameters["possible_exercises"]
        phase_components = parameters["phase_components"]
        workout_length = min(parameters["availability"], parameters["workout_length"])

        projected_duration = parameters["projected_duration"]

        longest_subcomponent_string_size = len(max(phase_components[1:], key=lambda d:len(d["name"]))["name"])
        longest_bodypart_string_size = len(max(phase_components[1:], key=lambda d:len(d["bodypart_name"]))["bodypart_name"])

        longest_pc_string_size = longest_subcomponent_string_size + longest_bodypart_string_size
        longest_exercise_string_size = len(max(exercises[1:], key=lambda d:len(d["name"]))["name"])

        used_days = []
        
        # Total time the user has to workout.
        formatted = "Optimization Results:\n"
        formatted += "=" * 50 + "\n\n"
        
        # Show relaxation attempts history
        formatted += "Relaxation Attempts:\n"
        formatted += "-" * 40 + "\n"
        for i, attempt in enumerate(state["relaxation_attempts"], 1):
            formatted += f"\nAttempt {i}:\n"
            formatted += f"Constraints relaxed: {attempt.constraints_relaxed}\n"
            formatted += f"Result: {'Feasible' if attempt.result_feasible else 'Infeasible'}\n"
            if workout_length is not None:
                formatted += f"Workout Length Allowed: {workout_length // 60} min {workout_length % 60} sec ({workout_length} seconds)\n"
            if attempt.duration is not None:
                formatted += f"Total Time Used: {attempt.duration // 60} min {attempt.duration % 60} sec ({attempt.duration} seconds)\n"
            if attempt.working_duration is not None:
                formatted += f"Total Time Worked: {attempt.working_duration // 60} min {attempt.working_duration % 60} sec ({attempt.working_duration} seconds)\n"
            if attempt.strain_ratio is not None:
                formatted += f"Total Strain: {attempt.strain_ratio}\n"
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
            
            for component_count, (i, exercise_index, phase_component_index, 
                    active_exercises, base_strain, seconds_per_exercise, 
                    reps_var, sets_var, rest_var, 
                    duration, working_duration) in enumerate(schedule):

                exercise = exercises[exercise_index]
                exercise_id = exercise["id"]
                phase_component = phase_components[phase_component_index]
                phase_component_id = phase_component["phase_component_id"]
                bodypart_id = phase_component["bodypart_id"]

                exercise_name = exercise["name"]
                phase_component_name = phase_component["name"] + " " + phase_component["bodypart_name"] 

                #duration = (bodypart_var * (seconds_per_exercise * reps_var + rest_var) * sets_var)

                if active_exercises:
                    final_output.append({
                        "i": i, 
                        "exercise_index": exercise_index,
                        "exercise_id": exercise_id,
                        "phase_component_index": phase_component_index, 
                        "phase_component_id": phase_component_id,
                        "bodypart_id": bodypart_id,
                        "base_strain": base_strain, 
                        "seconds_per_exercise": seconds_per_exercise, 
                        "active_exercises": active_exercises, 
                        "reps_var": reps_var, 
                        "sets_var": sets_var, 
                        "rest_var": rest_var, 
                        "duration": duration,
                        "working_duration": working_duration
                    })

                    # Count the number of occurrences of each phase component
                    phase_component_count[phase_component_index] += 1

                    formatted_exercise = f"{exercise_name:<{longest_exercise_string_size+3}}"
                    formatted_phase_component = f"{phase_component_name:<{longest_pc_string_size+3}}"

                    formatted_duration = f"Duration: {duration // 60} min {duration % 60} sec ({duration} seconds)\t"
                    formatted_working_duration = f"Work: {working_duration // 60} min {working_duration  % 60} sec ({working_duration:<{4}} seconds)\t"

                    formatted_base_strain = f"Base Strain {base_strain:<{3}}\t"
                    formatted_seconds_per_exercises = f"Sec/Exercise {seconds_per_exercise:<{5}}"
                    formatted_reps = f"Reps {reps_var:<{3}} ({phase_component["reps_min"]:<{3}}- {phase_component["reps_max"]:<{3}})\t"
                    formatted_sets = f"Sets {sets_var} ({phase_component["sets_min"]}- {phase_component["sets_max"]})\t"
                    formatted_rest = f"Rest {rest_var:<{3}} ({(phase_component["rest_min"] * 5):<{3}}-  {(phase_component["rest_max"] * 5):<{3}})"

                    formatted += (f"Exercise {(component_count + 1):<{2}}: {formatted_exercise}{formatted_base_strain}\n\t{formatted_phase_component}{formatted_duration}{formatted_working_duration}({formatted_seconds_per_exercises}{formatted_reps}{formatted_sets}{formatted_rest})\n")
                else:
                    formatted += (f"Exercise {(component_count + 1):<{2}} ----\n")

            formatted += f"Phase Component Counts:\n"
            for phase_component_index, phase_component_number in enumerate(phase_component_count):
                phase_component = phase_components[phase_component_index]
                formatted += f"\t{phase_component["name"] + " " + phase_component["bodypart_name"]:<{longest_pc_string_size+3}}: {phase_component_number}\n"
            formatted += f"Total Strain: {solution['strain_ratio']}\n"
            formatted += f"Projected Duration: {projected_duration // 60} min {projected_duration % 60} sec ({projected_duration}) seconds\n"
            formatted += f"Total Duration: {solution['duration'] // 60} min {solution['duration'] % 60} sec ({solution['duration']}) seconds\n"
            formatted += f"Total Work Duration: {solution['working_duration'] // 60} min {solution['working_duration']  % 60} sec ({solution['working_duration']}) seconds\n"
            formatted += f"Workout Length Allowed: {workout_length // 60} min {workout_length % 60} sec ({workout_length} seconds)\n"

            # Show final constraint status
            formatted += "\nFinal Constraint Status:\n"
            for constraint, active in state["constraints"].items():
                formatted += f"- {constraint}: {'Active' if active else 'Relaxed'}\n"

        return {"formatted": formatted, "output": final_output}

    def run(self):
        graph = self.create_optimization_graph(State)
        result = graph.invoke(self.initial_state)
        return result

def Main(parameters=None, constraints=None):
    agent = ExerciseAgent(parameters, constraints)
    result = agent.run()
    return {"formatted": result["formatted"], "output": result["output"], "solution": result["solution"]}

if __name__ == "__main__":
    result = Main()
    print(result["formatted"])
