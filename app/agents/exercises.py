from langgraph.graph import StateGraph, START, END
from ortools.sat.python import cp_model
from dotenv import load_dotenv
import math

from app.agents.constraints import (
    intvar_list_from_phase_components, 
    intvar_list_from_elements, 
    link_entry_and_item, 
    no_repeated_items, 
    only_use_required_items, 
    entries_equal)

from app.agents.exercise_model_specific_constraints import (
    create_exercise_intensity_var, 
    constrain_weighted_exercises_var, 
    constrain_intensity_vars, 
    constrain_training_weight_vars, 
    constrain_volume_vars, 
    constrain_density_vars, 
    constrain_performance_vars)

from app.agents.exercises_phase_components import RelaxationAttempt, State, ExercisePhaseComponentAgent, declare_duration_vars, get_phase_component_bounds
from app.utils.longest_string import longest_string_size_for_key
from app.utils.min_and_max_in_dict import get_item_bounds

_ = load_dotenv()

def get_exercises_for_pc_conditions(exercises, phase_component, conditions=[]):
    return [i for i, exercise in enumerate(exercises, start=1) 
            if all(f(exercise, phase_component) for f in conditions)]

def get_exercises_for_pc(exercises, phase_component):
    conditions = [lambda exercise, phase_component: exercise['component_id'] == phase_component["component_id"],
                  lambda exercise, phase_component: exercise['subcomponent_id'] == phase_component["subcomponent_id"],
                  lambda exercise, phase_component: (1 in exercise['bodypart_ids']) or (phase_component["bodypart_id"] in exercise["bodypart_ids"])]

    exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, conditions)
    print_check = False

    if (exercises_for_pc == []) and (phase_component["bodypart_id"] == 1):
        print(f"'{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']}' has no exercises for bodypart '{phase_component['bodypart_name']}', include all exercises for this component phase if it's total body.")
        print_check = True
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, conditions[0:2])

    if exercises_for_pc == []:
        print(f"'{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']}' still has no exercises for bodypart '{phase_component['bodypart_name']}', include all exercises.")
        print_check = True
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component)
    
    if print_check:
        print("")
    return exercises_for_pc

def ensure_increase_for_subcomponent(model, exercises, phase_components, phase_component_ids, used_exercise_vars, performance_vars, training_weight_vars):
    for phase_component_index, performance_var, used_exercise_var, training_weight_var in zip(phase_component_ids, performance_vars, used_exercise_vars, training_weight_vars):
        phase_component = phase_components[phase_component_index]
        volume_max = phase_component["volume_max"]
        density_max = phase_component["density_max"]

        for exercise_index, (exercise, exercise_for_exercise_var) in enumerate(zip(exercises[1:], used_exercise_var[1:])):
            if exercise["is_weighted"]:
                volume_max_training = round(volume_max  * (phase_component["intensity_max"] or 100) * exercise["one_rep_max"])
                performance_max = volume_max_training * density_max
            else:
                # Scale up to match the scale of the training weight volume
                volume_max_training = volume_max  * (100 * 100)
                performance_max = volume_max_training * density_max

            # Check to ensure that the performance doesn't exceed the maximum.
            performance_not_at_max = model.NewBoolVar(f'exercise_{exercise_index}_performance_max_for_pc_{phase_component_index}')
            model.Add(performance_var < performance_max).OnlyEnforceIf(performance_not_at_max)          # Performance must be less than or equal to the maximum performance possible.
            model.Add(performance_var >= performance_max).OnlyEnforceIf(performance_not_at_max.Not())   # Performance is greater than the maximum performance possible.

            # If the maximum is going to be reached, do not exceed it.
            model.Add(performance_var > exercise["performance"]).OnlyEnforceIf(exercise_for_exercise_var, performance_not_at_max)
            model.Add(performance_var == exercise["performance"]).OnlyEnforceIf(exercise_for_exercise_var, performance_not_at_max.Not())
    return None

def get_exercise_bounds(exercises):
    return {
        'base_strain': get_item_bounds("base_strain", "base_strain", exercises),
        'intensity': {"min": 1, "max": 100},
        'one_rep_max': get_item_bounds("one_rep_max", "one_rep_max", exercises)
    }

class ExerciseAgent(ExercisePhaseComponentAgent):
    def solve_model_node_temp(self, state: State, config=None) -> dict:
        print("Solving First Step")
        """Solve model and record relaxation attempt results."""
        model, phase_component_vars, used_pc_vars, active_exercise_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars, working_duration_vars = state["opt_model"]

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 24
        #solver.parameters.log_search_progress = True
        status = solver.Solve(model)

        state["logs"] += f"\nSolver status: {status}\n"
        state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            schedule = []
            # Each day in the microcycle
            for i in range(len(duration_vars)):
                model.AddHint(phase_component_vars[i], solver.Value(phase_component_vars[i]))

                # Ensure that the phase component is active.
                if(solver.Value(active_exercise_vars[i])):
                    schedule.append((
                        i, 
                        solver.Value(phase_component_vars[i]), 
                        solver.Value(active_exercise_vars[i]), 
                        solver.Value(seconds_per_exercise_vars[i]), 
                        solver.Value(reps_vars[i]), 
                        solver.Value(sets_vars[i]), 
                        solver.Value(rest_vars[i]) * 5, 
                        solver.Value(duration_vars[i]), 
                        solver.Value(working_duration_vars[i])
                    ))
            schedule = sorted(schedule, key=lambda x: x[1])
            solution = {
                "schedule": schedule,
                "status": status
            }

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

    def build_opt_model_node_2(self, state: State, config=None) -> dict:
        print("Building Second Step")

        """Build the optimization model with active constraints."""
        parameters = state["parameters"]
        constraints = state["constraints"]
        model = cp_model.CpModel()

        exercise_volume_improvement_percentage = parameters["exercise_volume_improvement_percentage"]

        exercises = parameters["possible_exercises"]
        exercise_amount = len(exercises)
        weighted_exercise_indices = [i for i, exercise in enumerate(exercises[1:], start=1) if exercise["is_weighted"]]

        phase_components = parameters["phase_components"]

        schedule_old = state["solution"]["schedule"]

        phase_component_ids = [phase_component_index for (_, phase_component_index, _, _, _, _, _, _, _) in (schedule_old)]


        # Define variables =====================================

        # Upper bound on number of exercises (greedy estimation)
        max_exercises = len(phase_component_ids)

        # Get the bounds for the phase components
        pc_bounds = get_phase_component_bounds(phase_components[1:])
        max_seconds_per_exercise = pc_bounds["seconds_per_exercise"]["max"]
        max_reps = pc_bounds["reps"]["max"]
        max_sets = pc_bounds["sets"]["max"]
        max_rest = pc_bounds["rest"]["max"]
        min_volume, max_volume = pc_bounds["volume"]["min"], pc_bounds["volume"]["max"]
        min_density, max_density = pc_bounds["density"]["min"], pc_bounds["density"]["max"]
        max_duration = pc_bounds["duration"]["max"]

        # Get the bounds for the exercises
        exercise_bounds = get_exercise_bounds(exercises[1:])
        min_base_strain, max_base_strain = exercise_bounds["base_strain"]["min"], exercise_bounds["base_strain"]["max"]
        min_intensity, max_intensity = exercise_bounds["intensity"]["min"], exercise_bounds["intensity"]["max"]
        min_one_rep_max, max_one_rep_max = exercise_bounds["one_rep_max"]["min"], exercise_bounds["one_rep_max"]["max"]

        min_training_weight_scaled = min_one_rep_max * min_intensity
        max_training_weight_scaled = max_one_rep_max * max_intensity

        min_volume = min_volume * min(min_training_weight_scaled, 1)
        max_volume = max_volume * max_training_weight_scaled

        max_strain_scaled = ((max_seconds_per_exercise * (10 + max_intensity + max_base_strain) * max_reps) + (10 *max_rest * 5)) * max_sets

        # Maximum amount of time that the workout may last
        workout_length = min(parameters["availability"], parameters["workout_length"])

        # Integer variable representing the phase component metrics chosen at exercise i.
        seconds_per_exercise_vars = intvar_list_from_phase_components(model, phase_component_ids, phase_components, "seconds_per_exercise", "seconds_per_exercise", "seconds_per_exercise")
        reps_vars = intvar_list_from_phase_components(model, phase_component_ids, phase_components, "reps", "reps_min", "reps_max")
        sets_vars = intvar_list_from_phase_components(model, phase_component_ids, phase_components, "sets", "sets_min", "sets_max")
        rest_vars = intvar_list_from_phase_components(model, phase_component_ids, phase_components, "rest", "rest_min", "rest_max")
        duration_vars = declare_duration_vars(model, max_exercises, workout_length, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, name="base")
        working_duration_vars = declare_duration_vars(model, max_exercises, workout_length, seconds_per_exercise_vars, reps_vars, sets_vars, name="working")

        # Integer variable representing the intensity chosen at exercise i.
        intensity_vars = [
            model.NewIntVar(0, (phase_components[pc_index]["intensity_max"] or 100), f'intensity_{i}')
            for i, pc_index in enumerate(phase_component_ids)]

        # Integer variable representing the exercise metrics chosen at exercise i.
        exercise_vars = intvar_list_from_elements(model, max_exercises, "exercise", 1, (exercise_amount - 1))
        base_strain_vars = intvar_list_from_elements(model, max_exercises, "base_strain", min_base_strain, max_base_strain)
        one_rep_max_vars = intvar_list_from_elements(model, max_exercises, "one_rep_max", min_one_rep_max, max_one_rep_max)
        training_weight_vars = intvar_list_from_elements(model, max_exercises, "training_weight", 0, max_training_weight_scaled)
        volume_vars = intvar_list_from_elements(model, max_exercises, "volume", min_volume, max_volume)
        density_vars = intvar_list_from_elements(model, max_exercises, "density", min_density, max_density)
        performance_vars = intvar_list_from_elements(model, max_exercises, "performance", min_density * min_volume, max_density * max_volume)

        # Boolean variable representing whether exercise i is weighted.
        weighted_exercise_vars = [
            model.NewBoolVar(f'exercise_{i}_is_weighted') 
            for i in range(max_exercises)]


        # Boolean variables indicating whether exercise type j is used at exercise i.
        used_exercise_vars = [[
            model.NewBoolVar(f'exercise_{i}_is_exercise_{j}')
            for j in range(exercise_amount)]
            for i in range(max_exercises)]

        constrain_weighted_exercises_var(model, used_exercise_vars, weighted_exercise_vars, weighted_exercise_indices)
        constrain_intensity_vars(model, intensity_vars, phase_component_ids, phase_components, weighted_exercise_vars)
        constrain_training_weight_vars(model, intensity_vars, exercises[1:], training_weight_vars, used_exercise_vars, weighted_exercise_vars)
        constrain_volume_vars(model, volume_vars, max_volume, reps_vars, sets_vars, training_weight_vars, weighted_exercise_vars)
        constrain_density_vars(model, density_vars, duration_vars, working_duration_vars, max_duration)
        constrain_performance_vars(model, performance_vars, volume_vars, density_vars)

        # Links the exercise variables and the exercises that can exist via the used exercises variables.
        link_entry_and_item(model = model, 
                            items = exercises, 
                            entry_vars = exercise_vars, 
                            number_of_entries = max_exercises, 
                            used_vars = used_exercise_vars)

        # Apply active constraints ======================================
        state["logs"] += "\nBuilding model with constraints:\n"

        # Ensure total time is within two minutes of the originally calculated duration.
        model.Add(sum(duration_vars) <= workout_length)
        model.Add(sum(duration_vars) >= (workout_length - (2 * 60)))

        # Constraint: The base strain of an exercise may only be equal to the base strain allowed for the exercise.
        if constraints["base_strain_equals"]:
            entries_equal(model = model, 
                          items = exercises, 
                          key="base_strain", 
                          number_of_entries = max_exercises, 
                          used_vars = used_exercise_vars, 
                          duration_vars = base_strain_vars)
            state["logs"] += "- Base strain equal to base strain allowed for exercise applied.\n"

        # Constraint: The 1RM of an exercise may only be equal to the one rep max allowed for the exercise.
        if constraints["one_rep_max_equals"]:
            entries_equal(model = model, 
                          items = exercises, 
                          key="one_rep_max", 
                          number_of_entries = max_exercises, 
                          used_vars = used_exercise_vars, 
                          duration_vars = one_rep_max_vars)
            state["logs"] += "- One rep max equal to one rep max allowed for exercise applied.\n"

        # Constraint: Use only allowed exercises
        if constraints["use_allowed_exercises"]:
            for i, phase_component_index in enumerate(phase_component_ids):
                exercises_for_pc = get_exercises_for_pc(exercises[1:], phase_components[phase_component_index])
                only_use_required_items(model = model, 
                                        required_items = exercises_for_pc, 
                                        entry_vars = [exercise_vars[i]])
            state["logs"] += "- Only use allowed exercises applied.\n"

        # Constraint: Ensure each exercise only appears once in the schedule
        if constraints["no_duplicate_exercises"]:
            required_phase_components = list(range(1, len(exercises)))
            no_repeated_items(model = model, 
                              required_items = required_phase_components, 
                              used_vars = used_exercise_vars)
            state["logs"] += "- No duplicate exercises constraint applied.\n"

        # Constraint: The desired metric of an exercise must be an increase from the current metric.
        if constraints["exercise_metric_increase"]:
            ensure_increase_for_subcomponent(model, exercises, phase_components, phase_component_ids, used_exercise_vars, performance_vars, training_weight_vars)
            state["logs"] += "- Exercise metric increase constraint applied.\n"

        # Objective: Maximize total strain of microcycle
        if constraints["minimize_strain"]:
            # List of contributions to goal time.
            strain_terms = []

            # Creates strain_time, which will hold the total strain over the workout.
            strain_time = model.NewIntVar(0, 100 * max_exercises * workout_length, 'strain_time')
            for i, values_for_exercise in enumerate(zip(base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, intensity_vars)):
                (
                    base_strain_var,
                    seconds_per_exercise_var, 
                    reps_var, 
                    sets_var, 
                    rest_var,
                    intensity_var
                ) = values_for_exercise
                # Create the entry for phase component's intensity
                # total_working_duration = (seconds_per_exercise*(1+.1*basestrain)* rep_count) * set_count
                non_zero_working_duration_var = model.NewIntVar(1, max_strain_scaled, f'non_zero_working_strained_duration_{i}')
                working_duration_is_0 = model.NewBoolVar(f'working_strained_duration_{i}_is_0')

                duration_var = create_exercise_intensity_var(
                    model=model, 
                    i=i, 
                    max_duration=max_strain_scaled, 
                    seconds_per_exercise=seconds_per_exercise_var, 
                    reps=reps_var, 
                    sets=sets_var, 
                    rest=rest_var,
                    intensity=intensity_var,
                    base_strain=base_strain_var,
                    name="base_strained")

                working_duration_var = create_exercise_intensity_var(
                    model=model, 
                    i=i, 
                    max_duration=max_strain_scaled, 
                    seconds_per_exercise=seconds_per_exercise_var, 
                    reps=reps_var, 
                    sets=sets_var, 
                    rest=0,
                    intensity=intensity_var,
                    base_strain=base_strain_var,
                    name="working_strained")

                # Ensure no division by 0 occurs.
                model.Add(non_zero_working_duration_var == 1).OnlyEnforceIf(working_duration_is_0)
                model.Add(non_zero_working_duration_var == working_duration_var).OnlyEnforceIf(working_duration_is_0.Not())
                model.Add(working_duration_var == 0).OnlyEnforceIf(working_duration_is_0)
                model.Add(working_duration_var >= 1).OnlyEnforceIf(working_duration_is_0.Not())

                strain = model.NewIntVar(0, 100 * workout_length, f'strain_{i}')
                model.AddDivisionEquality(strain, 100 * duration_var, non_zero_working_duration_var)

                strain_terms.append(strain)

            model.Add(strain_time == sum(strain_terms))
            model.Minimize(strain_time)

            state["logs"] += "- Minimizing the strain time used in workout.\n"

        return {"opt_model": (model, exercise_vars, phase_component_ids, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, intensity_vars, one_rep_max_vars, training_weight_vars, volume_vars, density_vars, performance_vars, duration_vars, working_duration_vars)}

    def solve_model_node(self, state: State, config=None) -> dict:
        print("Solving Second Step")
        """Solve model and record relaxation attempt results."""
        model, exercise_vars, phase_component_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, intensity_vars, one_rep_max_vars, training_weight_vars, volume_vars, density_vars, performance_vars, duration_vars, working_duration_vars = state["opt_model"]

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 24
        # solver.parameters.log_search_progress = True
        status = solver.Solve(model)

        state["logs"] += f"\nSolver status: {status}\n"
        state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            strain_ratio = duration = working_duration = 0
            schedule = []
            # Each day in the microcycle
            for i in range(len(duration_vars)):

                # Ensure that the phase component is active.
                duration_vars_current = solver.Value(duration_vars[i])
                working_duration_vars_current = solver.Value(working_duration_vars[i])

                schedule.append((
                    i, 
                    solver.Value(exercise_vars[i]),                                     # Index of the exercise chosen.
                    phase_component_vars[i],                                            # Index of the phase component chosen.
                    solver.Value(base_strain_vars[i]),                                  # Base strain of the exercise chosen.
                    solver.Value(seconds_per_exercise_vars[i]),                         # Seconds per exercise of the exercise chosen.
                    solver.Value(reps_vars[i]),                                         # Reps of the exercise chosen.
                    solver.Value(sets_vars[i]),                                         # Sets of the exercise chosen.
                    solver.Value(rest_vars[i]) * 5,                                     # Rest of the exercise chosen.
                    solver.Value(intensity_vars[i]),                                    # Intensity of the exercise chosen.
                    round(solver.Value(one_rep_max_vars[i]) / 100, 2),                  # 1RM of the exercise chosen. Scaled down due to scaling up of intensity.
                    round(solver.Value(training_weight_vars[i]) / (100 * 100), 2),      # Training weight of the exercise chosen. Scaled down due to scaling up of intensity AND training weight.
                    round(solver.Value(volume_vars[i]) / (100 * 100), 2),               # Volume of the exercise chosen.
                    round(solver.Value(density_vars[i]) / 100, 2),                      # Density of the exercise chosen. Scaled down due to scaling up division.
                    round(solver.Value(performance_vars[i]) / (100 * 100 * 100), 2),    # Performance of the exercise chosen. Scaled down due to scaling up of intensity AND training weight.
                    duration_vars_current,                                              # Duration of the exercise chosen.
                    working_duration_vars_current,                                      # Working duration of the exercise chosen.
                ))
                duration += duration_vars_current
                working_duration += working_duration_vars_current
                strain_ratio += duration_vars_current/working_duration_vars_current
            schedule = sorted(schedule, key=lambda x: x[2])
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

    def get_model_formatting_parameters(self, parameters):
        workout_length = min(parameters["availability"], parameters["workout_length"])
        return [
            parameters["phase_components"],
            parameters["possible_exercises"],
            parameters["projected_duration"],
            workout_length
        ]

    def format_agent_output(self, solution, formatted, schedule, phase_components, exercises, projected_duration, workout_length):
        final_output = []

        longest_subcomponent_string_size = longest_string_size_for_key(phase_components[1:], "name")
        longest_bodypart_string_size = longest_string_size_for_key(phase_components[1:], "bodypart_name")
        longest_pc_string_size = longest_subcomponent_string_size + longest_bodypart_string_size

        longest_exercise_string_size = longest_string_size_for_key(exercises[1:], "name")

        phase_component_count = [0] * len(phase_components)

        formatted += "\nFinal Training Schedule:\n"
        formatted += "-" * 120 + "\n"

        formatted_number_header = f"{"#":<{3}}"
        formatted_exercise_header = f"| {"Exercise":<{longest_exercise_string_size+2}}"
        formatted_phase_component_header = f"| {"Phase Component":<{longest_pc_string_size+2}}"
        formatted_duration_header = f"| {"Duration":<{10}}"
        formatted_working_duration_header = f"| {"WDuration":<{10}}"
        formatted_base_strain_header = f"| {"BStrain":<{8}}"
        formatted_seconds_per_exercises_header = f"| {"(Sec/Exercise":<{14}}"
        formatted_reps_header = f"| {"Reps":<{11}}"
        formatted_sets_header = f"| {"Sets":<{8}}"
        formatted_rest_header = f"| {"Rest)":<{15}}"
        formatted_one_rep_max_header = f"| {"1RM":<{15}}"
        formatted_training_weight_header = f"| {"Weight":<{8}}"
        formatted_intensity_header = f"| {"Intensity":<{12}}"
        formatted_volume_header = f"| {"Volume":<{25}}"
        formatted_density_header = f"| {"Density":<{22}}"
        formatted_performance_header = f"| {"Performance":<{30}}"

        formatted_phase_component_stats = f"{formatted_phase_component_header}{formatted_duration_header}{formatted_working_duration_header}{formatted_seconds_per_exercises_header}{formatted_reps_header}{formatted_sets_header}{formatted_rest_header}"
        formatted_improvement_metrics = f"{formatted_one_rep_max_header}{formatted_training_weight_header}{formatted_intensity_header}{formatted_volume_header}{formatted_density_header}{formatted_performance_header}"

        formatted += (f"{formatted_number_header}{formatted_exercise_header}{formatted_base_strain_header}{formatted_phase_component_stats}{formatted_improvement_metrics}\n")

        for component_count, (i, exercise_index, phase_component_index, 
                base_strain, seconds_per_exercise, 
                reps_var, sets_var, rest_var, intensity_var, one_rep_max_var, 
                training_weight_var, volume_var, density_var, performance_var, 
                duration, working_duration) in enumerate(schedule):

            exercise = exercises[exercise_index]
            phase_component = phase_components[phase_component_index]

            phase_component_name = phase_component["name"] + " " + phase_component["bodypart_name"] 

            #duration = (bodypart_var * (seconds_per_exercise * reps_var + rest_var) * sets_var)
            final_output.append({
                "i": i, 
                "exercise_index": exercise_index,
                "exercise_id": exercise["id"],
                "phase_component_index": phase_component_index, 
                "phase_component_id": phase_component["phase_component_id"],
                "bodypart_id": phase_component["bodypart_id"],
                "base_strain": base_strain, 
                "seconds_per_exercise": seconds_per_exercise, 
                "reps_var": reps_var, 
                "sets_var": sets_var, 
                "rest_var": rest_var, 
                "intensity_var": intensity_var, 
                "one_rep_max_var": one_rep_max_var,
                "training_weight": training_weight_var,
                "volume": volume_var,
                "density": density_var,
                "performance": performance_var,
                "duration": duration,
                "working_duration": working_duration
            })

            # Count the number of occurrences of each phase component
            phase_component_count[phase_component_index] += 1

            formatted_component_count = f"{component_count + 1}"
            number_str = f"{formatted_component_count:<{len(formatted_number_header)}}"

            formatted_exercise = f"| {exercise["name"]}"
            exercise_str = f"{formatted_exercise:<{len(formatted_exercise_header)}}"

            formatted_phase_component = f"| {phase_component_name}"
            phase_component_str = f"{formatted_phase_component:<{len(formatted_phase_component_header)}}"

            formatted_duration = f"| {duration} sec"
            duration_str = f"{formatted_duration:<{len(formatted_duration_header)}}"

            formatted_working_duration = f"| {working_duration} sec"
            working_duration_str = f"{formatted_working_duration:<{len(formatted_working_duration_header)}}"

            formatted_base_strain = f"| {base_strain}"
            base_strain_str = f"{formatted_base_strain:<{len(formatted_base_strain_header)}}"

            formatted_seconds_per_exercises = f"| ({seconds_per_exercise} sec"
            seconds_per_exercises_str = f"{formatted_seconds_per_exercises:<{len(formatted_seconds_per_exercises_header)}}"

            formatted_reps = f"| {reps_var} ({phase_component["reps_min"]}-{phase_component["reps_max"]})"
            reps_str = f"{formatted_reps:<{len(formatted_reps_header)}}"

            formatted_sets = f"| {sets_var} ({phase_component["sets_min"]}-{phase_component["sets_max"]})"
            sets_str = f"{formatted_sets:<{len(formatted_sets_header)}}"

            formatted_rest = f"| {rest_var} ({phase_component["rest_min"] * 5}-{phase_component["rest_max"] * 5})"
            rest_str = f"{formatted_rest+")":<{len(formatted_rest_header)}}"

            formatted_one_rep_max = ""
            formatted_training_weight = ""

            formatted_intensity = ""
            volume_max = phase_component["volume_max"]
            if intensity_var:
                volume_max = round(volume_max * (exercise["one_rep_max"] / 100) * ((phase_component["intensity_max"] or 100) / 100))
                formatted_one_rep_max = f"{one_rep_max_var} -> {round((training_weight_var * (30 + reps_var)) / 30, 2)}"
                formatted_training_weight = f"{training_weight_var}"
                formatted_intensity = f"{intensity_var} ({phase_component["intensity_min"] or 1}-{phase_component["intensity_max"] or 100})"

            one_rep_max_str = f"{"| " + formatted_one_rep_max:<{len(formatted_one_rep_max_header)}}"
            training_weight_str = f"{"| " + formatted_training_weight:<{len(formatted_training_weight_header)}}"
            intensity_str = f"{"| " + formatted_intensity:<{len(formatted_intensity_header)}}"

            formatted_volume = f"| {exercise["volume"] / (100 * 100)} -> {volume_var} (>={volume_max})"
            volume_str = f"{formatted_volume:<{len(formatted_volume_header)}}"

            density_max = phase_component["density_max"] / 100

            formatted_density = f"| {exercise["density"] / 100} -> {density_var} (>={density_max})"
            density_str = f"{formatted_density:<{len(formatted_density_header)}}"

            performance_max = round(volume_max * density_max * 100) / 100
            formatted_performance = f"| {(exercise["performance"] / (100 * 100 * 100))} -> {performance_var} (>={performance_max})"
            performance_str = f"{formatted_performance:<{len(formatted_performance_header)}}"

            formatted_phase_component_stats = f"{phase_component_str}{duration_str}{working_duration_str}{seconds_per_exercises_str}{reps_str}{sets_str}{rest_str}"
            formatted_improvement_metrics = f"{one_rep_max_str}{training_weight_str}{intensity_str}{volume_str}{density_str}{performance_str}"

            formatted += (f"{number_str}{exercise_str}{base_strain_str}{formatted_phase_component_stats}{formatted_improvement_metrics}\n")

        formatted += f"Phase Component Counts:\n"
        for phase_component_index, phase_component_number in enumerate(phase_component_count):
            phase_component = phase_components[phase_component_index]
            phase_component_name = f"{phase_component["name"] + " " + phase_component["bodypart_name"]:<{longest_pc_string_size+3}}"
            formatted += f"\t{phase_component_name}: {self._format_range(phase_component_number, phase_component["exercises_per_bodypart_workout_min"], phase_component["exercises_per_bodypart_workout_max"])}\n"
        formatted += f"Total Strain: {solution['strain_ratio']}\n"
        formatted += f"Projected Duration: {self._format_duration(projected_duration)}\n"
        formatted += f"Total Duration: {self._format_duration(solution['duration'])}\n"
        formatted += f"Total Work Duration: {self._format_duration(solution['working_duration'])}\n"
        formatted += f"Workout Length Allowed: {self._format_duration(workout_length)}\n"
        return final_output, formatted

    def create_optimization_graph(self, state_class):
        builder = StateGraph(state_class)

        # Add common nodes
        builder.add_node("setup", self.setup_params_node)
        builder.add_node("build_1", self.build_opt_model_node)
        builder.add_node("solve_1", self.solve_model_node_temp)
        builder.add_node("analyze", self.analyze_infeasibility_node)

        builder.add_node("build_2", self.build_opt_model_node_2)
        builder.add_node("solve_2", self.solve_model_node)
        builder.add_node("format", self.format_solution_node)

        # Add common edges
        builder.add_edge(START, "setup")
        builder.add_edge("setup", "build_1")
        builder.add_edge("build_1", "solve_1")

        builder.add_conditional_edges(
            "solve_1",
            self.solution_router,
            {
                "analyze": "analyze",
                "format": "build_2"
            }
        )

        builder.add_edge("build_2", "solve_2")

        builder.add_conditional_edges(
            "solve_2",
            self.solution_router,
            {
                "analyze": "analyze",
                "format": "format"
            }
        )

        builder.add_edge("analyze", "build_1")

        builder.add_edge("format", END)

        return builder.compile()

def Main(parameters=None, constraints=None):
    agent = ExerciseAgent(parameters, constraints)
    result = agent.run()
    return {"formatted": result["formatted"], "output": result["output"], "solution": result["solution"]}

if __name__ == "__main__":
    result = Main()
    print(result["formatted"])
