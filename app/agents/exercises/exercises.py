from config import ortools_solver_time_in_seconds, verbose, log_schedule, log_steps, log_details
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
    entries_equal, 
    retrieve_indication_of_increase)

from app.agents.exercises.exercise_model_specific_constraints import (
    constrain_duration_var, 
    create_exercise_effort_var, 
    constrain_weighted_exercises_var, 
    constrain_intensity_vars, 
    constrain_scaled_training_weight_vars, 
    constrain_training_weight_vars, 
    constrain_volume_vars, 
    constrain_density_vars, 
    constrain_performance_vars)

from .exercises_phase_components import RelaxationAttempt, State, ExercisePhaseComponentAgent
from app.utils.longest_string import longest_string_size_for_key
from .get_pc_exercise_bounds import get_bounds

_ = load_dotenv()

def declare_duration_vars(model, max_entries, phase_component_ids, phase_components, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars=None, name=""):
    return [
        constrain_duration_var(
            model=model, i=i, 
            phase_component_constraints=phase_components[phase_component_ids[i]], 
            seconds_per_exercise=seconds_per_exercise_vars[i], 
            reps=reps_vars[i], 
            sets=sets_vars[i], 
            rest=rest_vars[i] if rest_vars is not None else 0,
            name=name,
            working=False if rest_vars is not None else True)
        for i in range(max_entries)]

def declare_effort_vars(model, max_entries, ex_bounds, phase_component_ids, phase_components, seconds_per_exercise_vars, reps_vars, sets_vars, intensity_vars, base_strain_vars, rest_vars=None, name=""):
    return [
        create_exercise_effort_var(
            model=model, i=i, 
            phase_component_constraints=phase_components[phase_component_ids[i]], 
            exercise_bounds=ex_bounds, 
            seconds_per_exercise=seconds_per_exercise_vars[i], 
            reps=reps_vars[i], 
            sets=sets_vars[i], 
            rest=rest_vars[i] if rest_vars is not None else 0,
            intensity=intensity_vars[i],
            base_strain=base_strain_vars[i],
            name=name,
            working=False if rest_vars is not None else True)
        for i in range(max_entries)]

def encourage_increase_for_subcomponent(model, exercises, phase_component_ids, used_exercise_vars, performance_vars, max_performance):
    return [
        retrieve_indication_of_increase(model, exercises, max_performance, pc_index, performance_var, used_exercise_var)
        for pc_index, performance_var, used_exercise_var in zip(phase_component_ids, performance_vars, used_exercise_vars)
    ]

class ExerciseAgent(ExercisePhaseComponentAgent):
    def solve_model_node_temp(self, state: State, config=None) -> dict:
        self._log_steps("Solving First Step")
        """Solve model and record relaxation attempt results."""
        #return {"solution": "None"}
        # model, model_with_divided_strain, phase_component_vars, pc_count_vars, active_exercise_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars, working_duration_vars = state["opt_model"]
        model, model_with_divided_strain, vars = state["opt_model"]
        phase_component_vars, pc_count_vars, active_exercise_vars = vars["phase_components"], vars["pc_count"], vars["active_exercises"]
        seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars = vars["seconds_per_exercise"], vars["reps"], vars["sets"], vars["rest"]
        volume_vars, density_vars, performance_vars = vars["volume"], vars["density"], vars["performance"]
        duration_vars, working_duration_vars = vars["duration"], vars["working_duration"]

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 24
        solver.parameters.max_time_in_seconds = ortools_solver_time_in_seconds
        # solver.parameters.log_search_progress = True
        status = self._solve_and_time_solver(solver, model)

        if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            status = self._new_max_time_solve_and_time_solver(solver, model_with_divided_strain, new_max_time=None, message_end="Solving with strain divided.")

        state["logs"] += f"\nSolver status: {status}\n"
        state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            schedule = []
            # Each day in the microcycle
            for i in range(len(duration_vars)):
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

    def create_model_pc_vars(self, model, phase_components, workout_availability, phase_component_ids, max_exercises):
        # Define variables =====================================
        pc_vars = {}

        # Integer variable representing the phase component metrics chosen at exercise i.
        pc_vars["seconds_per_exercise"] = intvar_list_from_phase_components(model, phase_component_ids, phase_components, "seconds_per_exercise", "seconds_per_exercise", "seconds_per_exercise")
        pc_vars["reps"] = intvar_list_from_phase_components(model, phase_component_ids, phase_components, "reps", "reps_min", "reps_max")
        pc_vars["sets"] = intvar_list_from_phase_components(model, phase_component_ids, phase_components, "sets", "sets_min", "sets_max")
        pc_vars["rest"] = intvar_list_from_phase_components(model, phase_component_ids, phase_components, "rest", "rest_min", "rest_max")
        pc_vars["duration"] = declare_duration_vars(model, max_exercises, phase_component_ids, phase_components, pc_vars["seconds_per_exercise"], pc_vars["reps"], pc_vars["sets"], pc_vars["rest"], name="base")
        pc_vars["working_duration"] = declare_duration_vars(model, max_exercises, phase_component_ids, phase_components, pc_vars["seconds_per_exercise"], pc_vars["reps"], pc_vars["sets"], name="working")

        # Integer variable representing the intensity chosen at exercise i.
        pc_vars["intensity"] = [
            model.NewIntVar(0, phase_components[pc_index]["intensity_max"], f'intensity_{i}')
            for i, pc_index in enumerate(phase_component_ids)]

        return pc_vars
    
    def create_model_exercise_vars(self, model, phase_component_ids, phase_components, pc_vars, pc_bounds, exercises, max_exercises, ex_bounds):
        exercise_amount = len(exercises)
        weighted_exercise_indices = [i for i, exercise in enumerate(exercises[1:], start=1) if exercise["is_weighted"]]

        # Get the bounds for the phase components
        volume_bounds, density_bounds, duration_bounds = pc_bounds["volume"], pc_bounds["density"], pc_bounds["duration"]

        # Get the bounds for the exercises
        base_strain_bounds = ex_bounds["base_strain"]
        one_rep_max_bounds = ex_bounds["one_rep_max"]
        training_weight_bounds = ex_bounds["training_weight"]
        performance_bounds = ex_bounds["performance"]

        # Define variables =====================================
        exercise_vars = {}

        # Integer variable representing the exercise metrics chosen at exercise i.
        exercise_vars["exercises"] = intvar_list_from_elements(model, max_exercises, "exercise", 1, (exercise_amount - 1))
        exercise_vars["base_strain"] = intvar_list_from_elements(model, max_exercises, "base_strain", base_strain_bounds["min"], base_strain_bounds["max"])
        exercise_vars["one_rep_max"] = intvar_list_from_elements(model, max_exercises, "one_rep_max", one_rep_max_bounds["min"], one_rep_max_bounds["max"])
        exercise_vars["training_weight"] = intvar_list_from_elements(model, max_exercises, "training_weight", 0, training_weight_bounds["max"])
        exercise_vars["training_weight_scaled"] = intvar_list_from_elements(model, max_exercises, "training_weight_scaled", 0, training_weight_bounds["max"] * 100)
        exercise_vars["volume"] = intvar_list_from_elements(model, max_exercises, "volume", volume_bounds["min"], volume_bounds["max"])
        exercise_vars["density"] = intvar_list_from_elements(model, max_exercises, "density", density_bounds["min"], density_bounds["max"])
        exercise_vars["performance"] = intvar_list_from_elements(model, max_exercises, "performance", performance_bounds["min"], performance_bounds["max"])

        # Scale down the true training weight.
        for training_weight_var, training_weight_scaled_var in zip(exercise_vars["training_weight"], exercise_vars["training_weight_scaled"]):
            model.AddDivisionEquality(training_weight_var, training_weight_scaled_var, 100)

        exercise_vars["base_effort"] = declare_effort_vars(model, max_exercises, ex_bounds, phase_component_ids, phase_components, pc_vars["seconds_per_exercise"], pc_vars["reps"], pc_vars["sets"], pc_vars["intensity"], exercise_vars["base_strain"], pc_vars["rest"], name="base_strained")
        exercise_vars["working_effort"] = declare_effort_vars(model, max_exercises, ex_bounds, phase_component_ids, phase_components, pc_vars["seconds_per_exercise"], pc_vars["reps"], pc_vars["sets"], pc_vars["intensity"], exercise_vars["base_strain"], name="working_strained")

        # Boolean variable representing whether exercise i is weighted.
        exercise_vars["weighted_exercises"] = [
            model.NewBoolVar(f'exercise_{i}_is_weighted') 
            for i in range(max_exercises)]


        # Boolean variables indicating whether exercise type j is used at exercise i.
        exercise_vars["used_exercises"] = [[
            model.NewBoolVar(f'exercise_{i}_is_exercise_{j}')
            for j in range(exercise_amount)]
            for i in range(max_exercises)]

        constrain_weighted_exercises_var(model, exercise_vars["used_exercises"], exercise_vars["weighted_exercises"], weighted_exercise_indices)
        constrain_intensity_vars(model, pc_vars["intensity"], phase_component_ids, phase_components, exercise_vars["weighted_exercises"])
        constrain_scaled_training_weight_vars(model, pc_vars["intensity"], exercises[1:], exercise_vars["training_weight_scaled"], exercise_vars["used_exercises"])
        constrain_training_weight_vars(model, exercises[1:], exercise_vars["training_weight"], exercise_vars["used_exercises"], exercise_vars["weighted_exercises"])
        constrain_volume_vars(model, exercise_vars["volume"], pc_vars["reps"], pc_vars["sets"], volume_bounds["max"], exercise_vars["training_weight"], exercise_vars["weighted_exercises"])
        constrain_density_vars(model, exercise_vars["density"], pc_vars["duration"], pc_vars["working_duration"], duration_bounds["max"])
        constrain_performance_vars(model, exercise_vars["performance"], exercise_vars["volume"], exercise_vars["density"])

        # Links the exercise variables and the exercises that can exist via the used exercises variables.
        link_entry_and_item(model = model, 
                            items = exercises, 
                            entry_vars = exercise_vars["exercises"], 
                            number_of_entries = max_exercises, 
                            used_vars = exercise_vars["used_exercises"])
        return exercise_vars


    def apply_model_constraints_2(self, constraints, model, phase_component_ids, phase_components, pc_vars, pc_bounds, exercises, exercise_vars, ex_bounds, max_exercises, workout_availability, projected_duration):
        # Apply active constraints ======================================
        logs = "\nBuilding model with constraints:\n"

        # Ensure total time is within two minutes of the originally calculated duration.
        model.Add(sum(pc_vars["duration"]) <= workout_availability)
        model.Add(sum(pc_vars["duration"]) >= (projected_duration - (2 * 60)))

        # Constraint: The base strain of an exercise may only be equal to the base strain allowed for the exercise.
        if constraints["base_strain_equals"]:
            entries_equal(model = model, 
                          items = exercises, 
                          key="base_strain", 
                          number_of_entries = max_exercises, 
                          used_vars = exercise_vars["used_exercises"], 
                          duration_vars = exercise_vars["base_strain"])
            logs += "- Base strain equal to base strain allowed for exercise applied.\n"

        # Constraint: The 1RM of an exercise may only be equal to the one rep max allowed for the exercise.
        if constraints["one_rep_max_equals"]:
            entries_equal(model = model, 
                          items = exercises, 
                          key="one_rep_max", 
                          number_of_entries = max_exercises, 
                          used_vars = exercise_vars["used_exercises"], 
                          duration_vars = exercise_vars["one_rep_max"])
            logs += "- One rep max equal to one rep max allowed for exercise applied.\n"

        # Constraint: Use only allowed exercises
        if constraints["use_allowed_exercises"]:
            for i, phase_component_index in enumerate(phase_component_ids):
                pc = phase_components[phase_component_index]
                only_use_required_items(model = model, 
                                        required_items = pc["allowed_exercises"], 
                                        entry_vars = [exercise_vars["exercises"][i]])

            logs += "- Only use allowed exercises applied.\n"

        # Constraint: Ensure each exercise only appears once in the schedule
        if constraints["no_duplicate_exercises"]:
            required_phase_components = list(range(1, len(exercises)))
            no_repeated_items(model = model, 
                              required_items = required_phase_components, 
                              used_vars = exercise_vars["used_exercises"])
            logs += "- No duplicate exercises constraint applied.\n"

        # Constraint: The desired metric of an exercise must be an increase from the current metric.
        exercise_vars["performance_increase_penalty"] = None
        penalty = 100
        if constraints["exercise_metric_increase"]:
            performance_increase_conditions = encourage_increase_for_subcomponent(model, exercises, phase_component_ids, exercise_vars["used_exercises"], exercise_vars["performance"], ex_bounds["performance"]["max"])
            exercise_vars["performance_increase_penalty"] = [
                penalty * i
                for i in performance_increase_conditions
            ]
            logs += "- Exercise metric increase constraint applied.\n"
        return logs

    def effort_strain_as_sum(self, model, exercise_vars, exercise_bounds, max_exercises, workout_availability):
        # Get the bounds for the phase components
        min_effort_scaled = exercise_bounds["effort"]["min"]
        max_effort_scaled = exercise_bounds["effort"]["max"]
        max_strain_scaled = exercise_bounds["max_strain"]

        # SOLUTION 2
        total_working_effort = model.NewIntVar(max_exercises * min_effort_scaled, max_exercises * max_effort_scaled, 'total_working_effort')
        total_base_effort = model.NewIntVar(max_exercises * min_effort_scaled, max_exercises * max_effort_scaled, 'total_base_effort')

        model.Add(total_working_effort == sum(exercise_vars["working_effort"]))
        model.Add(total_base_effort == sum(exercise_vars["base_effort"]))

        # Create the entry for phase component's intensity
        # total_working_duration = (seconds_per_exercise*(1+.1*basestrain)* rep_count) * set_count
        non_zero_total_effort = model.NewIntVar(1, max_exercises * max_strain_scaled, f'non_zero_total_effort')
        total_effort_is_0 = model.NewBoolVar(f'total_effort_is_0')

        # Ensure no division by 0 occurs.
        model.Add(non_zero_total_effort == 1).OnlyEnforceIf(total_effort_is_0)
        model.Add(non_zero_total_effort == total_base_effort).OnlyEnforceIf(total_effort_is_0.Not())
        model.Add(total_base_effort == 0).OnlyEnforceIf(total_effort_is_0)
        model.Add(total_base_effort >= 1).OnlyEnforceIf(total_effort_is_0.Not())

        # Creates strain_time, which will hold the total strain over the workout.
        strain_time = model.NewIntVar(0, 100 * max_exercises * workout_availability, 'strain_time')
        model.AddDivisionEquality(strain_time, 100 * total_working_effort, non_zero_total_effort)
        total_strain_to_minimize = strain_time

        # Use Penalty.
        if exercise_vars["performance_increase_penalty"] != None:
            total_strain_to_minimize += sum(exercise_vars["performance_increase_penalty"])

        model.Minimize(total_strain_to_minimize)
        exercise_vars["strain_time"] = strain_time
        return None

    def effort_strain_divided(self, model, exercise_vars, exercise_bounds, max_exercises):
        # Get the bounds for the phase components
        max_effort_scaled = exercise_bounds["effort"]["max"]
        max_strain_scaled = exercise_bounds["max_strain"]

        # List of contributions to goal time.
        strain_terms = []

        # Creates strain_time, which will hold the total strain over the workout.
        strain_time = model.NewIntVar(0, 100 * max_exercises * max_strain_scaled, 'strain_time')
        for i, (base_effort_var, working_effort_var) in enumerate(zip(exercise_vars["base_effort"], exercise_vars["working_effort"])):
            # Create the entry for phase component's intensity
            # total_working_duration = (seconds_per_exercise*(1+.1*basestrain)* rep_count) * set_count
            non_zero_base_effort_var = model.NewIntVar(1, max_effort_scaled, f'non_zero_base_effort_{i}')
            base_effort_is_0 = model.NewBoolVar(f'base_effort_{i}_is_0')

            # Ensure no division by 0 occurs.
            model.Add(non_zero_base_effort_var == 1).OnlyEnforceIf(base_effort_is_0)
            model.Add(non_zero_base_effort_var == base_effort_var).OnlyEnforceIf(base_effort_is_0.Not())
            model.Add(base_effort_var == 0).OnlyEnforceIf(base_effort_is_0)
            model.Add(base_effort_var >= 1).OnlyEnforceIf(base_effort_is_0.Not())

            strain = model.NewIntVar(0, 100 * max_strain_scaled, f'strain_{i}')
            model.AddDivisionEquality(strain, 100 * working_effort_var, non_zero_base_effort_var)

            strain_terms.append(strain)

        model.Add(strain_time == sum(strain_terms))
        total_strain_to_minimize = strain_time

        # Use Penalty.
        if exercise_vars["performance_increase_penalty"] != None:
            total_strain_to_minimize += sum(exercise_vars["performance_increase_penalty"])

        model.Minimize(total_strain_to_minimize)
        exercise_vars["strain_time"] = strain_time
        return None

    def apply_model_objective_2(self, constraints, model, model_with_divided_strain, pc_vars, pc_bounds, exercise_vars, exercise_bounds, max_exercises, workout_availability):
        logs = ""
        # Objective: Maximize total strain of microcycle
        if constraints["minimize_strain"]:
            self.effort_strain_divided(model_with_divided_strain, exercise_vars, exercise_bounds, max_exercises)
            self.effort_strain_as_sum(model, exercise_vars, exercise_bounds, max_exercises, workout_availability)
            logs += "- Minimizing the strain time used in workout.\n"
        return logs

    def build_opt_model_node_2(self, state: State, config=None) -> dict:
        self._log_steps("Building Second Step")

        """Build the optimization model with active constraints."""
        parameters = state["parameters"]
        constraints = state["constraints"]
        model = cp_model.CpModel()
        model_with_divided_strain = cp_model.CpModel()

        exercise_volume_improvement_percentage = parameters["exercise_volume_improvement_percentage"]

        exercises = parameters["possible_exercises"]
        phase_components = parameters["phase_components"]
        workout_availability = parameters["availability"]
        projected_duration = parameters["projected_duration"]
        schedule_old = state["solution"]["schedule"]

        phase_component_ids = [phase_component_index for (_, phase_component_index, _, _, _, _, _, _, _) in (schedule_old)]

        # Upper bound on number of exercises (greedy estimation)
        max_exercises = len(phase_component_ids)

        pc_bounds, exercise_bounds = get_bounds(phase_components[1:], exercises[1:])

        pc_vars = self.create_model_pc_vars(model, phase_components, workout_availability, phase_component_ids, max_exercises)
        exercise_vars = self.create_model_exercise_vars(model, phase_component_ids, phase_components, pc_vars, pc_bounds, exercises, max_exercises, exercise_bounds)

        state["logs"] += self.apply_model_constraints_2(constraints, model, phase_component_ids, phase_components, pc_vars, pc_bounds, exercises, exercise_vars, exercise_bounds, max_exercises, workout_availability, projected_duration)
        model_with_divided_strain = model.clone()
        state["logs"] += self.apply_model_objective_2(constraints, model, model_with_divided_strain, pc_vars, pc_bounds, exercise_vars, exercise_bounds, max_exercises, workout_availability)

        return {"opt_model": (model, model_with_divided_strain, phase_component_ids, exercise_vars, pc_vars)}

    def solve_model_node(self, state: State, config=None) -> dict:
        self._log_steps("Solving Second Step")
        """Solve model and record relaxation attempt results."""
        model, model_with_divided_strain, phase_component_vars, ex_vars, pc_vars = state["opt_model"]
        exercise_vars, base_strain_vars, one_rep_max_vars, training_weight_vars, is_weighted_vars, volume_vars, density_vars, performance_vars = ex_vars["exercises"], ex_vars["base_strain"], ex_vars["one_rep_max"], ex_vars["training_weight"], ex_vars["weighted_exercises"], ex_vars["volume"], ex_vars["density"], ex_vars["performance"]
        seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, intensity_vars, duration_vars, working_duration_vars = pc_vars["seconds_per_exercise"], pc_vars["reps"], pc_vars["sets"], pc_vars["rest"], pc_vars["intensity"], pc_vars["duration"], pc_vars["working_duration"]
        base_effort_vars, working_effort_vars = ex_vars["base_effort"], ex_vars["working_effort"]

        parameters = state["parameters"]
        exercises = parameters["possible_exercises"]
        phase_components = parameters["phase_components"]
        pc_bounds, exercise_bounds = get_bounds(phase_components[1:], exercises[1:])
        max_strain_scaled = exercise_bounds["max_strain"]

        # Upper bound on number of exercises (greedy estimation)
        max_exercises = len(exercise_vars)
        workout_availability = parameters["availability"]

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 24
        solver.parameters.max_time_in_seconds = ortools_solver_time_in_seconds
        # solver.parameters.log_search_progress = True
        status = self._solve_and_time_solver(solver, model)
        max_strain_calc = 100 * max_exercises * workout_availability

        if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            status = self._new_max_time_solve_and_time_solver(solver, model, new_max_time=60)

        if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            status = self._new_max_time_solve_and_time_solver(solver, model_with_divided_strain, new_max_time=(10 * 60), message_end="Solving with strain divided.")
            max_strain_calc = max_exercises * max_strain_scaled

        state["logs"] += f"\nSolver status: {status}\n"
        state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            strain_ratio = duration = working_duration = base_effort = working_effort = 0
            schedule = []
            # Each day in the microcycle
            for i in range(len(duration_vars)):

                # Ensure that the phase component is active.
                duration_vars_current = solver.Value(duration_vars[i])
                working_duration_vars_current = solver.Value(working_duration_vars[i])
                base_effort_vars_current = solver.Value(base_effort_vars[i])
                working_effort_vars_current = solver.Value(working_effort_vars[i])

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
                    solver.Value(one_rep_max_vars[i]),                                  # 1RM of the exercise chosen. Scaled down due to scaling up of intensity.
                    solver.Value(training_weight_vars[i]),                              # Training weight of the exercise chosen. Scaled down due to scaling up of intensity AND training weight.
                    solver.Value(is_weighted_vars[i]),                                  # Whether the exercise chosen was weighted.
                    solver.Value(volume_vars[i]),                                       # Volume of the exercise chosen.
                    round(solver.Value(density_vars[i]) / 100, 2),                      # Density of the exercise chosen. Scaled down due to scaling up division.
                    round((solver.Value(performance_vars[i]) / 100), 2),                # Performance of the exercise chosen. Scaled down due to scaling up of intensity AND training weight.
                    duration_vars_current,                                              # Duration of the exercise chosen.
                    working_duration_vars_current,                                      # Working duration of the exercise chosen.
                ))
                duration += duration_vars_current
                working_duration += working_duration_vars_current

                base_effort += base_effort_vars_current
                working_effort += working_effort_vars_current

                strain_ratio += working_effort_vars_current/base_effort_vars_current
            schedule = sorted(schedule, key=lambda x: x[2])
            solution = {
                "schedule": schedule,
                "duration": duration,
                "working_duration": working_duration,
                "base_effort": base_effort,
                "working_effort": working_effort,
                "strain_ratio": working_duration/duration,
                "strain_calc": solver.Value(ex_vars["strain_time"]),
                "max_strain_calc": max_strain_calc,
                "status": status
            }

            # Record successful attempt
            attempt = RelaxationAttempt(
                state["current_attempt"]["constraints"],
                True,
                working_duration/duration,
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
        return [
            parameters["phase_components"],
            parameters["possible_exercises"],
            parameters["projected_duration"],
            parameters["availability"]
        ]

    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("", 5),
            "exercise": ("Exercise", longest_sizes["exercise"] + 4),
            "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
            "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
            "duration": ("Duration", 12),
            "working_duration": ("WDuration", 12),
            "base_strain": ("BStrain", 10),
            "seconds_per_exercise": ("(Sec/Exercise", 16),
            "reps": ("Reps", 14),
            "sets": ("Sets", 10),
            "rest": ("Rest)", 17),
            "one_rep_max": ("1RM", 17),
            "training_weight": ("Weight", 9),
            "intensity": ("Intensity", 14),
            "volume": ("Volume", 24),
            "density": ("Density", 24),
            "performance": ("Performance", 30)
        }

    def formatted_schedule(self, headers, component_count, phase_component, exercise, metrics):
        (base_strain, seconds_per_exercise, 
         reps_var, sets_var, rest_var, intensity_var, 
         one_rep_max_var, training_weight_var, is_weighted_var, 
         volume_var, density_var, 
         performance_var, duration, working_duration) = metrics
        one_rep_max_new = 0
        volume_max = phase_component["volume_max"]
        if is_weighted_var:
            one_rep_max_new = int(round((training_weight_var * (30 + reps_var)) / 30, 2))
            volume_max = round(volume_max * exercise["one_rep_max"] * (phase_component["intensity_max"] / 100))
        density_max = phase_component["density_max"] / 100
        performance_max = round(volume_max * density_max * 100) / 100

        # Format line
        line_fields = {
            "number": str(component_count + 1),
            "exercise": exercise["name"],
            "phase_component": f"{phase_component['name']}",
            "bodypart": phase_component["bodypart_name"],
            "duration": f"({duration} sec",
            "working_duration": f"({working_duration} sec",
            "base_strain": str(base_strain),
            "seconds_per_exercise": f"({seconds_per_exercise} sec",
            "reps": self._format_range(reps_var, phase_component["reps_min"], phase_component["reps_max"]),
            "sets": self._format_range(sets_var, phase_component["sets_min"], phase_component["sets_max"]),
            "rest": self._format_range(rest_var, phase_component["rest_min"] * 5, phase_component["rest_max"] * 5) + ")",
            "one_rep_max": f"{one_rep_max_var} -> {one_rep_max_new}" if intensity_var else "",
            "training_weight": str(training_weight_var) if intensity_var else "",
            "intensity": self._format_range(intensity_var, phase_component["intensity_min"] or 1, phase_component["intensity_max"]) if intensity_var else "",
            "volume": f"{exercise["volume"]} -> {volume_var} (>={volume_max})",
            "density": f"{exercise["density"] / 100} -> {density_var} (>={density_max})",
            "performance": f"{exercise["performance"] / 100} -> {performance_var} (>={performance_max})",
        }

        line = ""
        for field, (_, length) in headers.items():
            line += self._create_formatted_field(field, line_fields[field], length)
        return line + "\n"

    def format_agent_output(self, solution, formatted, schedule, phase_components, exercises, projected_duration, workout_availability):
        final_output = []

        phase_component_count = [0] * len(phase_components)

        # Calculate longest string sizes
        longest_sizes = {
            "phase_component": longest_string_size_for_key(phase_components[1:], "name"),
            "bodypart": longest_string_size_for_key(phase_components[1:], "bodypart_name"),
            "exercise": longest_string_size_for_key(exercises[1:], "name")
        }

        # Create headers
        headers = self._create_header_fields(longest_sizes)
        
        # Create header line
        if log_schedule: 
            formatted += self.formatted_header_line(headers)

        for component_count, (i, exercise_index, phase_component_index, *metrics) in enumerate(schedule):
            exercise = exercises[exercise_index]
            phase_component = phase_components[phase_component_index]

            (base_strain, seconds_per_exercise, 
             reps_var, sets_var, rest_var, intensity_var, 
             one_rep_max_var, training_weight_var, is_weighted_var, 
             volume_var, density_var, 
             performance_var, duration, working_duration) = metrics

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

            if log_schedule:
                formatted += self.formatted_schedule(headers, component_count, phase_component, exercise, metrics)

        if log_details:
            formatted += f"Phase Component Counts:\n"
            for phase_component_index, phase_component_number in enumerate(phase_component_count):
                phase_component = phase_components[phase_component_index]
                phase_component_name = f"{phase_component['name']:<{longest_sizes['phase_component']+2}} {phase_component['bodypart_name']:<{longest_sizes['bodypart']+2}}"
                formatted += f"\t{phase_component_name}: {self._format_range(phase_component_number, phase_component["exercises_per_bodypart_workout_min"], phase_component["exercises_per_bodypart_workout_max"])}\n"
            formatted += f"Total Strain: {solution['strain_ratio']}\n"
            formatted += f"Total Strain Solution 2: {solution['working_effort'] / solution['base_effort']}\n"
            formatted += f"Total Strain Scaled: {solution['strain_calc']} >= {solution['max_strain_calc']}\n"
            formatted += f"Projected Duration: {self._format_duration(projected_duration)}\n"
            formatted += f"Total Duration: {self._format_duration(solution['duration'])}\n"
            formatted += f"Total Work Duration: {self._format_duration(solution['working_duration'])}\n"
            formatted += f"Total Base Effort: {solution['base_effort']}\n"
            formatted += f"Total Working Effort: {solution['working_effort']}\n"
            formatted += f"Workout Length Allowed: {self._format_duration(workout_availability)}\n"
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
