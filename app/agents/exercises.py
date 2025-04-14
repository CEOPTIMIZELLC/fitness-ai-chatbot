from langgraph.graph import StateGraph, START, END
from ortools.sat.python import cp_model
from typing import Set, Optional
from dotenv import load_dotenv
from app.agents.constraints import (
    link_entry_and_item, 
    create_exercise_intensity_var, 
    no_repeated_items, 
    only_use_required_items, 
    entries_equal, 
    entries_within_min_max)
from app.agents.exercises_phase_components import RelaxationAttempt, State, ExercisePhaseComponentAgent, declare_model_vars, declare_duration_vars, format_relaxation_attempts
from app.agents.agent_helpers import longest_string_size_for_key

_ = load_dotenv()

def get_exercises_for_pc(exercises, phase_component):
    exercises_for_pc = [
        i for i, exercise in enumerate(exercises, start=1)
        if (exercise['component_id']==phase_component["component_id"] 
            and exercise['subcomponent_id']==phase_component["subcomponent_id"]
            and ((1 in exercise['bodypart_ids']) or
                 (phase_component["bodypart_id"] in exercise["bodypart_ids"])))]
    if (exercises_for_pc == []) and (phase_component["bodypart_id"] == 1):
        print(f"'{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']}' has no exercises for bodypart '{phase_component['bodypart_name']}', include all exercises for this component phase if it's total body.")
        exercises_for_pc = [
            i for i, exercise in enumerate(exercises, start=1)
            if (exercise['component_id']==phase_component["component_id"] 
                and exercise['subcomponent_id']==phase_component["subcomponent_id"])]
    if exercises_for_pc == []:
        print(f"'{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']}' still has no exercises for bodypart '{phase_component['bodypart_name']}', include all exercises.")
        exercises_for_pc = [i for i, _ in enumerate(exercises, start=1)]
    return exercises_for_pc

# Due to inability to make an expression as a constraint in a single line, a few steps must be taken prior.
# This method performs the in between steps and returns the final variable for the right side of the one rep formula.
# 1RM < (weight * (30 + reps)) / 30
def weight_rep_construction(model, i, 
                            one_rep_max, min_one_rep_max, max_one_rep_max, 
                            reps, min_reps, max_reps, 
                            weight, min_weight, max_weight, 
                            name=""):
    return None

def one_rep_max_increase(model, 
                         one_rep_max_vars, min_one_rep_max, max_one_rep_max, 
                         reps_vars, min_reps, max_reps, 
                         training_weight_vars, min_weight, max_weight):
    # Link the exercise variables and the training weight variables by ensuring the training weight is equal to the one rep max * intensity for the exercise chose at exercise i.
    for i, (one_rep_max_var, reps_var, training_weight_var) in enumerate(zip(one_rep_max_vars, reps_vars, training_weight_vars)):
        if training_weight_var != None:
            weight_rep_construction(model=model, 
                                    i=i, 
                                    one_rep_max=one_rep_max_var, 
                                    min_one_rep_max=min_one_rep_max, 
                                    max_one_rep_max=max_one_rep_max, 
                                    reps=reps_var, 
                                    min_reps=min_reps, 
                                    max_reps=max_reps, 
                                    weight=training_weight_var, 
                                    min_weight=min_weight, 
                                    max_weight=max_weight)
    return None


def format_agent_output_2(solution, formatted, schedule, phase_components, exercises, projected_duration, workout_length):
    final_output = []

    longest_subcomponent_string_size = longest_string_size_for_key(phase_components[1:], "name")
    longest_bodypart_string_size = longest_string_size_for_key(phase_components[1:], "bodypart_name")
    longest_pc_string_size = longest_subcomponent_string_size + longest_bodypart_string_size

    longest_exercise_string_size = longest_string_size_for_key(exercises[1:], "name")

    phase_component_count = [0] * len(phase_components)

    formatted += "\nFinal Training Schedule:\n"
    formatted += "-" * 40 + "\n"

    for component_count, (i, exercise_index, phase_component_index, 
            base_strain, seconds_per_exercise, 
            reps_var, sets_var, rest_var, intensity_var, one_rep_max_var, training_weight_var, 
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
            "duration": duration,
            "working_duration": working_duration
        })

        # Count the number of occurrences of each phase component
        phase_component_count[phase_component_index] += 1

        formatted_exercise = f"{exercise["name"]:<{longest_exercise_string_size+3}}"
        formatted_phase_component = f"{phase_component_name:<{longest_pc_string_size+3}}"

        formatted_duration = f"Duration: {duration // 60} min {duration % 60} sec ({duration} seconds)"
        formatted_base_strain = f"Base Strain {base_strain:<{3}}\t"
        formatted_seconds_per_exercises = f"Sec/Exercise {seconds_per_exercise:<{5}}"
        formatted_reps = f"Reps {reps_var} ({phase_component["reps_min"]}-{phase_component["reps_max"]})"
        formatted_sets = f"Sets {sets_var} ({phase_component["sets_min"]}-{phase_component["sets_max"]})"
        formatted_rest = f"Rest {rest_var} ({phase_component["rest_min"] * 5}-{phase_component["rest_max"] * 5})"
        formatted_one_rep_max = ""
        formatted_training_weight = ""
        formatted_intensity = ""
        if intensity_var != None:
            formatted_one_rep_max = f"1RM: {one_rep_max_var} -> {round((training_weight_var * (30 + reps_var)) / 30, 2)}"
            formatted_training_weight = f"Training Weight: {training_weight_var}"
            formatted_intensity = f"Intensity {intensity_var} ({phase_component["intensity_min"]}-{phase_component["intensity_max"]})"

        formatted += (f"Exercise {(component_count + 1):<{2}}: {formatted_exercise}{formatted_base_strain}{formatted_phase_component}{formatted_duration:<{45}}({formatted_seconds_per_exercises}{formatted_reps:<{20}}{formatted_sets:<{15}}{formatted_rest:<{20}}{formatted_one_rep_max:<{15}}{formatted_training_weight:<{25}}{formatted_intensity:<{6}})\n")

    formatted += f"Phase Component Counts:\n"
    for phase_component_index, phase_component_number in enumerate(phase_component_count):
        phase_component = phase_components[phase_component_index]
        formatted += f"\t{phase_component["name"] + " " + phase_component["bodypart_name"]:<{longest_pc_string_size+3}}: {phase_component_number} ({phase_component["exercises_per_bodypart_workout_min"]}-{phase_component["exercises_per_bodypart_workout_max"]})\n"
    formatted += f"Total Strain: {solution['strain_ratio']}\n"
    formatted += f"Projected Duration: {projected_duration // 60} min {projected_duration % 60} sec ({projected_duration}) seconds\n"
    formatted += f"Total Duration: {solution['duration'] // 60} min {solution['duration'] % 60} sec ({solution['duration']}) seconds\n"
    formatted += f"Total Work Duration: {solution['working_duration'] // 60} min {solution['working_duration']  % 60} sec ({solution['working_duration']}) seconds\n"
    formatted += f"Workout Length Allowed: {workout_length // 60} min {workout_length % 60} sec ({workout_length} seconds)\n"
    return final_output, formatted

class ExerciseAgent(ExercisePhaseComponentAgent):
    def solve_model_node_temp(self, state: State, config=None) -> dict:
        print("Solving First Step")
        """Solve model and record relaxation attempt results."""
        model, phase_component_vars, used_pc_vars, active_exercise_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars = state["opt_model"]

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
                        solver.Value(duration_vars[i])
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

        exercises = parameters["possible_exercises"]
        exercise_amount = len(exercises)

        phase_components = parameters["phase_components"]
        projected_duration = parameters["projected_duration"]

        schedule_old = state["solution"]["schedule"]

        phase_component_ids = []

        for (_, phase_component_index, _, _, _, _, _, _) in (schedule_old):
            phase_component_ids.append(phase_component_index)


        # Define variables =====================================

        # Upper bound on number of exercises (greedy estimation)
        max_exercises = len(phase_component_ids)
        max_seconds_per_exercise = max(phase_component["seconds_per_exercise"] for phase_component in phase_components[1:])
        min_reps = min(phase_component["reps_min"] for phase_component in phase_components[1:])
        max_reps = max(phase_component["reps_max"] for phase_component in phase_components[1:])
        max_sets = max(phase_component["sets_max"] for phase_component in phase_components[1:])
        max_rest = max(phase_component["rest_max"] for phase_component in phase_components[1:])
        max_intensity = 100
        min_base_strain = min(exercise["base_strain"] for exercise in exercises[1:])
        max_base_strain = max(exercise["base_strain"] for exercise in exercises[1:])
        min_one_rep_max = min(exercise["one_rep_max"] for exercise in exercises[1:])
        max_one_rep_max = max(exercise["one_rep_max"] for exercise in exercises[1:])
        min_training_weight_scaled = min_one_rep_max * 1
        max_training_weight_scaled = max_one_rep_max * max_intensity
        # min_one_rep_max = 100 * min_one_rep_max
        # max_one_rep_max = 100 * max_one_rep_max
        max_strain_scaled = ((max_seconds_per_exercise * (10 + max_intensity + max_base_strain) * max_reps) + (10 *max_rest * 5)) * max_sets

        # Maximum amount of time that the workout may last
        workout_length = min(parameters["availability"], parameters["workout_length"])

        # Integer variable representing the seconds_per_exercise chosen at exercise i.
        seconds_per_exercise_vars = [
            model.NewIntVar(phase_components[pc_index]["seconds_per_exercise"], phase_components[pc_index]["seconds_per_exercise"], f'seconds_per_exercise_{i}') 
            for i, pc_index in enumerate(phase_component_ids)]

        # Integer variable representing the reps chosen at exercise i.
        reps_vars = [
            model.NewIntVar(phase_components[pc_index]["reps_min"], phase_components[pc_index]["reps_max"], f'reps_{i}') 
            for i, pc_index in enumerate(phase_component_ids)]

        # Integer variable representing the sets chosen at exercise i.
        sets_vars = [
            model.NewIntVar(phase_components[pc_index]["sets_min"], phase_components[pc_index]["sets_max"], f'sets_{i}') 
            for i, pc_index in enumerate(phase_component_ids)]

        # Integer variable representing the rest chosen at exercise i.
        rest_vars = [
            model.NewIntVar(phase_components[pc_index]["rest_min"], phase_components[pc_index]["rest_max"], f'rest_{i}') 
            for i, pc_index in enumerate(phase_component_ids)]

        duration_vars = declare_duration_vars(model, max_exercises, workout_length, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars)

        # Integer variable representing the intensity chosen at exercise i.
        intensity_vars = [
            model.NewIntVar((phase_components[pc_index]["intensity_min"] or 1), (phase_components[pc_index]["intensity_max"] or 100), f'intensity_{i}')
            if phase_components[pc_index]["intensity_min"] is not None and phase_components[pc_index]["intensity_max"] is not None
            else None #model.NewIntVar(0, 0, f'intensity_{i}')
            for i, pc_index in enumerate(phase_component_ids)]

        # Integer variable representing the exercise chosen at exercise i.
        exercise_vars = [
            model.NewIntVar(1, (exercise_amount - 1), f'exercise_{i}') 
            for i in range(max_exercises)]

        # Integer variable representing the base strain chosen at exercise i.
        base_strain_vars = [
            model.NewIntVar(min_base_strain, max_base_strain, f'base_strain_{i}') 
            for i in range(max_exercises)]

        # Integer variable representing the 1RM chosen at exercise i.
        one_rep_max_vars = [
            model.NewIntVar(min_one_rep_max, max_one_rep_max, f'one_rep_max_{i}') 
            for i in range(max_exercises)]

        # Boolean variables indicating whether exercise type j is used at exercise i.
        used_exercise_vars = [[
            model.NewBoolVar(f'exercise_{i}_is_exercise_{j}')
            for j in range(exercise_amount)]
            for i in range(max_exercises)]

        # Integer variable representing the training weight for the intensity chosen at exercise i.
        training_weight_vars = [
            model.NewIntVar(min_training_weight_scaled, max_training_weight_scaled, f'training_weight_{i}')
            if intensity_var is not None
            else None
            for i, intensity_var in enumerate(intensity_vars)]

        # Link the exercise variables and the training weight variables by ensuring the training weight is equal to the one rep max * intensity for the exercise chose at exercise i.
        for intensity_var, training_weight_var, used_exercise_var in zip(intensity_vars, training_weight_vars, used_exercise_vars):
            if training_weight_var != None :
                for exercise, exercise_for_exercise_var in zip(exercises[1:], used_exercise_var[1:]):
                    model.Add(training_weight_var == (exercise["one_rep_max"] * intensity_var)).OnlyEnforceIf(exercise_for_exercise_var)

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
        model.Add(sum(duration_vars) >= (projected_duration - (2 * 60)))

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
        
        # Constraint: 
        if constraints["one_rep_max_increase"]:
            one_rep_max_increase(model=model, 
                                 one_rep_max_vars=one_rep_max_vars, 
                                 min_one_rep_max=min_one_rep_max, 
                                 max_one_rep_max=max_one_rep_max, 
                                 reps_vars=reps_vars, 
                                 min_reps=min_reps, 
                                 max_reps=max_reps, 
                                 training_weight_vars=training_weight_vars, 
                                 min_weight=min_training_weight_scaled, 
                                 max_weight=max_training_weight_scaled)
            state["logs"] += "- One rep max increase constraint applied.\n"


        # Objective: Maximize total strain of microcycle
        if constraints["minimize_strain"]:
            # List of contributions to goal time.
            strain_terms = []

            # Creates strain_time, which will hold the total strain over the workout.
            strain_time = model.NewIntVar(0, max_exercises * workout_length, 'strain_time')
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
                non_zero_working_duration_var = model.NewIntVar(1, max_strain_scaled, f'non_zero_working_duration_{i}')
                working_duration_is_0 = model.NewBoolVar(f'working_duration_{i}_is_0')

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
                    name="base")

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
                    name="working")

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

            state["logs"] += "- Minimizing the strain time used in workout.\n"

        return {"opt_model": (model, exercise_vars, phase_component_ids, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, intensity_vars, one_rep_max_vars, training_weight_vars, duration_vars)}

    def solve_model_node(self, state: State, config=None) -> dict:
        print("Solving Second Step")
        """Solve model and record relaxation attempt results."""
        model, exercise_vars, phase_component_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, intensity_vars, one_rep_max_vars, training_weight_vars, duration_vars = state["opt_model"]

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
                seconds_per_exercise_current = solver.Value(seconds_per_exercise_vars[i])
                reps_vars_current = solver.Value(reps_vars[i])
                sets_vars_current = solver.Value(sets_vars[i])
                intensity_var_current = solver.Value(intensity_vars[i]) if intensity_vars[i] is not None else 0
                training_weight_var_current = solver.Value(training_weight_vars[i]) if training_weight_vars[i] is not None else 0
                duration_vars_current = solver.Value(duration_vars[i])
                working_duration_vars_current = (seconds_per_exercise_current * reps_vars_current * sets_vars_current)

                schedule.append((
                    i, 
                    solver.Value(exercise_vars[i]), 
                    phase_component_vars[i], 
                    solver.Value(base_strain_vars[i]), 
                    seconds_per_exercise_current, 
                    reps_vars_current, 
                    sets_vars_current, 
                    solver.Value(rest_vars[i]) * 5, 
                    intensity_var_current, 
                    solver.Value(one_rep_max_vars[i]),
                    training_weight_var_current / 100,
                    duration_vars_current,
                    working_duration_vars_current
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

    def format_solution_node_2(self, state: State, config=None) -> dict:
        print("Formatting Second Step")
        """Format the optimization results."""
        solution, parameters = state["solution"], state["parameters"]

        exercises, phase_components, projected_duration = parameters["possible_exercises"], parameters["phase_components"], parameters["projected_duration"]
        workout_length = min(parameters["availability"], parameters["workout_length"])

        # Total time the user has to workout.
        formatted = "Optimization Results:\n"
        formatted += "=" * 50 + "\n\n"

        # Show relaxation attempts history
        formatted = format_relaxation_attempts(state["relaxation_attempts"], formatted, workout_length)

        if solution is None:
            final_output = []
            formatted += "\nNo valid schedule found even with relaxed constraints.\n"
        else:
            schedule = solution["schedule"]
            final_output, formatted = format_agent_output_2(solution, formatted, schedule, phase_components, exercises, projected_duration, workout_length)

            # Show final constraint status
            formatted += self.format_constraint_status(state["constraints"])

        return {"formatted": formatted, "output": final_output}


    def create_optimization_graph(self, state_class):
        builder = StateGraph(state_class)

        # Add common nodes
        builder.add_node("setup", self.setup_params_node)
        builder.add_node("build_1", self.build_opt_model_node)
        builder.add_node("solve_1", self.solve_model_node_temp)
        builder.add_node("analyze", self.analyze_infeasibility_node)

        builder.add_node("build_2", self.build_opt_model_node_2)
        builder.add_node("solve_2", self.solve_model_node)
        builder.add_node("format", self.format_solution_node_2)

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
