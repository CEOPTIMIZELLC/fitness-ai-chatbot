from config import ortools_solver_time_in_seconds, verbose, log_schedule, log_steps, log_details
from ortools.sat.python import cp_model
from typing import Set, Optional
from app.agents.constraints import (
    entries_equal, 
    entries_within_min_max, 
    link_entry_and_item, 
    constrain_active_entries_vars, 
    create_optional_intvar, 
    declare_model_vars, 
    use_all_required_items, 
    exercises_per_bodypart_within_min_max, 
    symmetry_breaking_constraints, 
    add_tight_bounds, 
    retrieve_indication_of_increase)

from app.agents.exercises.exercise_model_specific_constraints import (
    constrain_duration_var, 
    create_exercise_effort_var, 
    constrain_weighted_exercises_var, 
    constrain_intensity_vars, 
    constrain_training_weight_vars, 
    constrain_volume_vars, 
    constrain_density_vars, 
    constrain_performance_vars)

from app.agents.exercises.exercise_model_specific_constraints import create_duration_var

from app.agents.base_agent import BaseRelaxationAttempt, BaseAgent, BaseAgentState
from app.utils.longest_string import longest_string_size_for_key
from .get_pc_exercise_bounds import get_phase_component_bounds

available_constraints = """
- use_all_phase_components: Forces all phase components to be assigned at least once in a workout.
- base_strain_equals: Forces the amount of base strain to be between the minimum and maximum values allowed for the exercise.
- use_allowed_exercises: Forces the exercise to be one of the exercises allowed for the phase component and bodypart combination.
- no_duplicate_exercises: Forces each exercise to only appear once in the schedule.
- secs_equals: Forces the number of seconds per exercise to be between the minimum and maximum values allowed for the phase component.
- reps_within_min_max: Forces the number of reps to be between the minimum and maximum values allowed for the phase component.
- sets_within_min_max: Forces the number of sets to be between the minimum and maximum values allowed for the phase component.
- rest_within_min_max: Forces the amount of rest to be between the minimum and maximum values allowed for the phase component.
- resistances_have_equal_sets: Forces all exercises for resistance components to have the same number of sets.
- resistances_have_equal_counts: Forces all phase components of different subcomponent types to have the same quantity if they are resistance components.
- duration_within_min_max: Forces the amount of duration to be between the minimum and maximum values allowed for the phase component.
- exercises_per_bodypart_within_min_max: Forces the number of exercises for a phase component to be between the minimum and maximum values allowed.
- exercise_metric_increase: Forces the prioritized metric of an exercise chosen to increase.
- minimize_strain: Objective to minimize the amount of strain overall.
"""

class RelaxationAttempt(BaseRelaxationAttempt):
    def __init__(self, 
                 constraints_relaxed: Set[str], 
                 result_feasible: bool, 
                 strain_ratio: Optional[int] = None,
                 duration: Optional[int] = None,
                 working_duration: Optional[int] = None,
                 reasoning: Optional[str] = None, 
                 expected_impact: Optional[str] = None):
        super().__init__(constraints_relaxed, result_feasible, reasoning, expected_impact)
        self.strain_ratio = strain_ratio
        self.duration = duration
        self.working_duration = working_duration

def declare_duration_vars(model, max_entries, max_duration, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars=None, name=""):
    return [
        create_duration_var(
            model=model, i=i, 
            max_duration=max_duration, 
            seconds_per_exercise=seconds_per_exercise_vars[i], 
            reps=reps_vars[i], 
            sets=sets_vars[i], 
            rest=rest_vars[i] if rest_vars is not None else 0,
            name=name)
        for i in range(max_entries)]

def encourage_increase_for_subcomponent(model, pcs, used_pc_vars, performance_vars, max_performance):
    return [
        retrieve_indication_of_increase(model, pcs, max_performance, pc_index, performance_var, used_pc_var)
        for pc_index, (performance_var, used_pc_var) in enumerate(zip(performance_vars, used_pc_vars))
    ]

class State(BaseAgentState):
    parameter_input: dict

class ExercisePhaseComponentAgent(BaseAgent):
    available_constraints = available_constraints

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
            "projected_duration": 0,
            "projected_duration": 0,
            "exercise_volume_improvement_percentage": 0,
            "phase_components": [],
            "possible_exercises": []
        }

        # Define all constraints with their active status
        constraints = {
            "duration_within_availability": True,           # The time of a workout won't exceed the time allowed for that given day.
            "use_allowed_exercises": True,                  # Only use exercises that are allowed for the phase component and bodypart combination.
            "no_duplicate_exercises": True,                 # Ensure each exercise only appears once
            "use_all_phase_components": True,               # At least one exercise should be given each phase component.
            "base_strain_equals": True,                     # The base strain of the exercise may only be a number equal to the base strain allowed for the exercise.
            "one_rep_max_equals": True,                     # The 1RM of the exercise may only be a number equal to the 1RM allowed for the exercise selected.
            "secs_equals": True,                            # The number of seconds per exercise of the exercise may only be a number equal to the seconds allowed for the phase component.
            "reps_within_min_max": True,                    # The number of reps of the exercise may only be a number between the minimum and maximum reps allowed for the phase component.
            "sets_within_min_max": True,                    # The number of sets of the exercise may only be a number between the minimum and maximum sets allowed for the phase component.
            "rest_within_min_max": True,                    # The number of rest of the exercise may only be a number between the minimum and maximum rest allowed for the phase component.
            "resistances_have_equal_sets": True,            # Forces all exercises for resistance components to have the same number of sets.
            "resistances_have_equal_counts": True,          # Forces all phase components of different subcomponent types to have the same quantity if they are resistance components.
            "duration_within_min_max": True,                # The number of duration of the exercise may only be a number between the minimum and maximum duration allowed for the phase component.
            "intensity_within_min_max": True,               # The amount of intensity for the exercise may only be a number between the minimum and maximum intensity allowed for the phase component.
            "exercises_per_bodypart_within_min_max": True,  # The number of exercises for the phase components of the exercise may only be a number between the minimum and maximum exercises per bodypart allowed for the phase component.
            "exercise_metric_increase": True,               # The prioritized metric of the exercise must be an increase from the current metric.
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
    
    def create_model_vars(self, model, phase_components, workout_availability, phase_component_amount, pc_bounds, min_exercises, max_exercises):
        seconds_per_exercise_bounds = pc_bounds["seconds_per_exercise"]
        reps_bounds, sets_bounds, rest_bounds = pc_bounds["reps"], pc_bounds["sets"], pc_bounds["rest"]
        volume_bounds, density_bounds, duration_bounds = pc_bounds["volume"], pc_bounds["density"], pc_bounds["duration"]
        performance_bounds = pc_bounds["performance"]

        # Define variables =====================================
        vars = {}

        # Boolean variables indicating whether exercise i is active.
        vars["active_exercises"] = [
            model.NewBoolVar(f'exercise_{i}_is_active') 
            for i in range(max_exercises)]

        # Optional integer variable for the phase component chosen at exercise i.
        vars["phase_components"] = declare_model_vars(model, "phase_component", vars["active_exercises"], max_exercises, 1, (phase_component_amount - 1))

        # Boolean variables indicating whether phase component j is used at exercise i.
        vars["used_pcs"] = [[
            model.NewBoolVar(f'exercise_{i}_is_phase_component_{j}')
            for j in range(phase_component_amount)]
            for i in range(max_exercises)]

        # Integer variable indicating the number of occurences of each phase component.
        vars["pc_count"] = [
            model.NewIntVar(0, phase_component_amount, f'pc_{i}_count') 
            for i in list(range(len(phase_components)))]

        # Optional integer variable for the phase component values chosen at exercise i.
        vars["seconds_per_exercise"] = declare_model_vars(model, "seconds_per_exercise", vars["active_exercises"], max_exercises, seconds_per_exercise_bounds["min"], seconds_per_exercise_bounds["max"])
        vars["reps"] = declare_model_vars(model, "reps", vars["active_exercises"], max_exercises, reps_bounds["min"], reps_bounds["max"])
        vars["sets"] = declare_model_vars(model, "sets", vars["active_exercises"], max_exercises, sets_bounds["min"], sets_bounds["max"])
        vars["rest"] = declare_model_vars(model, "rest", vars["active_exercises"], max_exercises, rest_bounds["min"], rest_bounds["max"])
        vars["volume"] = declare_model_vars(model, "volume", vars["active_exercises"], max_exercises, volume_bounds["min"], volume_bounds["max"])
        vars["density"] = declare_model_vars(model, "density", vars["active_exercises"], max_exercises, density_bounds["min"], density_bounds["max"])
        vars["performance"] = declare_model_vars(model, "performance", vars["active_exercises"], max_exercises, performance_bounds["min"], performance_bounds["max"])

        # duration_vars = declare_duration_vars(model, max_exercises, workout_availability, vars["seconds_per_exercise"], vars["reps"], vars["sets"], vars["rest"])
        vars["duration"] = declare_duration_vars(model, max_exercises, workout_availability, vars["seconds_per_exercise"], vars["reps"], vars["sets"], vars["rest"], name="base")
        vars["working_duration"] = declare_duration_vars(model, max_exercises, workout_availability, vars["seconds_per_exercise"], vars["reps"], vars["sets"], name="working")

        # Introduce dynamic selection variables
        num_exercises_used = model.NewIntVar(min_exercises, max_exercises, 'num_exercises_used')
        model.Add(num_exercises_used == sum(vars["active_exercises"]))

        constrain_volume_vars(model, vars["volume"], vars["reps"], vars["sets"], volume_bounds["max"])
        constrain_density_vars(model, vars["density"], vars["duration"], vars["working_duration"], duration_bounds["max"])
        constrain_performance_vars(model, vars["performance"], vars["volume"], vars["density"])

        # Links the phase components variables and the phase components via the used phase components variables.
        link_entry_and_item(model = model, 
                            items = phase_components, 
                            entry_vars = vars["phase_components"], 
                            number_of_entries = max_exercises, 
                            used_vars = vars["used_pcs"])
        
        # Sets the counts for the variables.
        for item_index in list(range(len(phase_components))):
            conditions = [row[item_index] for row in vars["used_pcs"]]
            vars["pc_count"][item_index] = sum(conditions)

        # Constrain the active exercises to be within the duration of the workout.
        constrain_active_entries_vars(model = model, 
                                      entry_vars = vars["phase_components"], 
                                      number_of_entries = max_exercises, 
                                      duration_vars = vars["duration"], 
                                      active_entry_vars = vars["active_exercises"])
        return vars
    
    def apply_model_constraints(self, constraints, model, vars, phase_components, workout_availability, max_exercises, projected_duration):
        # Apply active constraints ======================================
        logs = "\nBuilding model with constraints:\n"

        # Ensure total time is within two minutes of the originally calculated duration.
        model.Add(sum(vars["duration"]) <= workout_availability)
        model.Add(sum(vars["duration"]) >= (projected_duration - (2 * 60)))

        vars["phase_component_use_penalty"] = None
        pc_use_penalty_scale = 2

        # Constraint: Use all required phases at least once
        if constraints["use_all_phase_components"]:
            required_phase_components = list(range(1, len(phase_components)))

            phase_component_use_conditionals = use_all_required_items(model = model, 
                                                                      required_items = required_phase_components, 
                                                                      used_vars = vars["used_pcs"], 
                                                                      soft_constraint=True)
            vars["phase_component_use_penalty"] = [
                pc_use_penalty_scale * (1-i)
                for i in phase_component_use_conditionals
            ]
            logs += "- Use every required phase at least once applied.\n"

        # Constraint: The seconds per exercise of a phase component may only be between the minimum and maximum seconds per exercise allowed.
        if constraints["secs_equals"]:
            entries_equal(model = model, 
                          items = phase_components, 
                          key="seconds_per_exercise", 
                          number_of_entries = max_exercises, 
                          used_vars = vars["used_pcs"], 
                          duration_vars = vars["seconds_per_exercise"])
            logs += "- Seconds per exercise count is equal to the seconds per exercise applied.\n"

        # Constraint: The reps of a phase component may only be a number of reps between the minimum and maximum reps allowed.
        if constraints["reps_within_min_max"]:
            entries_within_min_max(model = model, 
                                   items = phase_components, 
                                   minimum_key="reps_min", 
                                   maximum_key="reps_max",
                                   number_of_entries = max_exercises, 
                                   used_vars = vars["used_pcs"], 
                                   duration_vars = vars["reps"])
            logs += "- Reps count within min and max allowed reps applied.\n"

        # Constraint: The sets of a phase component may only be a number of sets between the minimum and maximum sets allowed.
        if constraints["sets_within_min_max"]:
            entries_within_min_max(model = model, 
                                   items = phase_components, 
                                   minimum_key="sets_min", 
                                   maximum_key="sets_max",
                                   number_of_entries = max_exercises, 
                                   used_vars = vars["used_pcs"], 
                                   duration_vars = vars["sets"])
            logs += "- Sets count within min and max allowed sets applied.\n"

        # Constraint: The rest of a phase component may only be a number of rest between the minimum and maximum rest allowed.
        if constraints["rest_within_min_max"]:
            entries_within_min_max(model = model, 
                                   items = phase_components, 
                                   minimum_key="rest_min", 
                                   maximum_key="rest_max",
                                   number_of_entries = max_exercises, 
                                   used_vars = vars["used_pcs"], 
                                   duration_vars = vars["rest"])
            logs += "- Rest count within min and max allowed rest applied.\n"

        # Constraint: The duration of a phase component may only be a number between the minimum and maximum duration allowed.
        if constraints["duration_within_min_max"]:
            entries_within_min_max(model = model, 
                                   items = phase_components, 
                                   minimum_key="duration_min", 
                                   maximum_key="duration_max",
                                   number_of_entries = max_exercises, 
                                   used_vars = vars["used_pcs"], 
                                   duration_vars = vars["duration"])
            logs += "- Duration amount within min and max allowed rest applied.\n"

        # Add symmetry breaking and tight bounds before applying main constraints
        symmetry_breaking_constraints(model, vars["phase_components"], vars["active_exercises"])
        phase_component_counts = add_tight_bounds(model = model, 
                                                  entry_vars = vars["phase_components"], 
                                                  used_vars = vars["used_pcs"], 
                                                  items = phase_components, 
                                                  minimum_key = "exercises_per_bodypart_workout_min", 
                                                  maximum_key = "exercises_per_bodypart_workout_max", 
                                                  name = "pc")

        # Constraint: The numer of exercises may only be a number of exercises between the minimum and maximum exercises per bodypart allowed.
        if constraints["exercises_per_bodypart_within_min_max"]:
            required_phase_components = list(range(1, len(phase_components)))
            exercises_per_bodypart_within_min_max(model=model, 
                                                  required_items=required_phase_components, 
                                                  items=phase_components, 
                                                  minimum_key="exercises_per_bodypart_workout_min", 
                                                  maximum_key="exercises_per_bodypart_workout_max", 
                                                  used_vars=vars["used_pcs"])
            logs += "- Exercises count within min and max allowed exercises applied (optimized).\n"
        
        # Constraint: The desired metric of an exercise must be an increase from the current metric.
        vars["performance_increase_penalty"] = None
        penalty = 100
        if constraints["exercise_metric_increase"]:
            performance_increase_conditions = encourage_increase_for_subcomponent(model, phase_components, vars["used_pcs"], vars["performance"], max(pc["performance"] for pc in phase_components[1:]))
            vars["performance_increase_penalty"] = [
                penalty * i
                for i in performance_increase_conditions
            ]
            logs += "- Exercise metric increase constraint applied.\n"
        return logs
    
    def duration_strain_as_sum(self, model, vars, workout_availability, pc_bounds, min_exercises, max_exercises):
        # max_duration = ((max_seconds_per_exercise * max_reps) + (max_rest * 5)) * max_sets
        duration_bounds = pc_bounds["duration"]
        working_duration_bounds = pc_bounds["working_duration"]
        total_working_duration_time = model.NewIntVar(1, max_exercises * working_duration_bounds["max"], 'total_working_duration_time')
        total_duration_time = model.NewIntVar(1, max_exercises * duration_bounds["max"], 'total_duration_time')

        model.Add(total_working_duration_time == sum(vars["working_duration"]))
        model.Add(total_duration_time == sum(vars["duration"]))

        non_zero_total_duration_time = model.NewIntVar(1, max_exercises * duration_bounds["max"], f'non_zero_total_duration_time')
        total_duration_is_0 = model.NewBoolVar(f'total_duration_time_is_0')

        # Ensure no division by 0 occurs.
        model.Add(non_zero_total_duration_time == 1).OnlyEnforceIf(total_duration_is_0)
        model.Add(non_zero_total_duration_time == total_duration_time).OnlyEnforceIf(total_duration_is_0.Not())
        model.Add(total_duration_time == 0).OnlyEnforceIf(total_duration_is_0)
        model.Add(total_duration_time >= 1).OnlyEnforceIf(total_duration_is_0.Not())

        strain = model.NewIntVar(0, 100 * max_exercises * workout_availability, f'strain_total')
        model.AddDivisionEquality(strain, 100 * total_working_duration_time, non_zero_total_duration_time)
        total_strain_to_minimize = strain

        # Use Penalty.
        if vars["phase_component_use_penalty"] != None:
            total_strain_to_minimize += sum(vars["phase_component_use_penalty"])

        model.Minimize(total_strain_to_minimize)
        return None
    
    def duration_strain_divided(self, model, vars, workout_availability, pc_bounds, min_exercises, max_exercises):
        # max_duration = ((max_seconds_per_exercise * max_reps) + (max_rest * 5)) * max_sets
        duration_bounds = pc_bounds["duration"]
        working_duration_bounds = pc_bounds["working_duration"]

        # List of contributions to goal time.
        strain_terms = []

        # Creates strain_time, which will hold the total strain over the workout.
        strain_time = model.NewIntVar(0, 100 * max_exercises * workout_availability, 'strain_time')
        for i, (base_duration_var, working_duration_var) in enumerate(zip(vars["duration"], vars["working_duration"])):
            # Create the entry for phase component's duration
            # total_working_duration = (seconds_per_exercise * rep_count) * set_count
            non_zero_base_duration_var = model.NewIntVar(1, duration_bounds["max"], f'non_zero_base_duration_{i}')
            base_duration_is_0 = model.NewBoolVar(f'base_duration_{i}_is_0')

            # Ensure no division by 0 occurs.
            model.Add(non_zero_base_duration_var == 1).OnlyEnforceIf(base_duration_is_0)
            model.Add(non_zero_base_duration_var == base_duration_var).OnlyEnforceIf(base_duration_is_0.Not())
            model.Add(base_duration_var == 0).OnlyEnforceIf(base_duration_is_0)
            model.Add(base_duration_var >= 1).OnlyEnforceIf(base_duration_is_0.Not())

            strain = model.NewIntVar(0, 100 * workout_availability, f'strain_{i}')
            model.AddDivisionEquality(strain, 100 * working_duration_var, non_zero_base_duration_var)

            strain_terms.append(strain)

        model.Add(strain_time == sum(strain_terms))
        total_strain_to_minimize = strain_time

        # Use Penalty.
        if vars["phase_component_use_penalty"] != None:
            total_strain_to_minimize += sum(vars["phase_component_use_penalty"])

        model.Minimize(total_strain_to_minimize)
        return None

    
    def app_model_objective(self, constraints, model, model_with_divided_strain, vars, workout_availability, pc_bounds, min_exercises, max_exercises, ):
        logs = ""
        # Objective: Minimize total strain of microcycle
        if constraints["minimize_strain"]:
            self.duration_strain_divided(model_with_divided_strain, vars, workout_availability, pc_bounds, min_exercises, max_exercises)
            self.duration_strain_as_sum(model, vars, workout_availability, pc_bounds, min_exercises, max_exercises)
            logs += "- Minimizing the strain time used in workout.\n"
        return logs

    def build_opt_model_node(self, state: State, config=None) -> dict:
        self._log_steps("Building First Step")
        """Build the optimization model with active constraints."""
        parameters = state["parameters"]
        constraints = state["constraints"]
        model = cp_model.CpModel()
        model_with_divided_strain = cp_model.CpModel()

        phase_components = parameters["phase_components"]
        phase_component_amount = len(phase_components)

        projected_duration = parameters["projected_duration"]

        # Maximum amount of time that the workout may last
        workout_availability = parameters["availability"]

        # Upper bound on number of exercises (greedy estimation)
        min_exercises = sum((phase_component["exercises_per_bodypart_workout_min"] or 1) for phase_component in phase_components[1:])
        max_exercises = sum((phase_component["exercises_per_bodypart_workout_max"] or 1) for phase_component in phase_components[1:])
        pc_bounds = get_phase_component_bounds(phase_components[1:])
        pc_bounds["performance"] = {"min": pc_bounds["volume"]["min"] * pc_bounds["density"]["min"], 
                                    "max": pc_bounds["volume"]["max"] * pc_bounds["density"]["max"]}

        vars = self.create_model_vars(model, phase_components, workout_availability, phase_component_amount, pc_bounds, min_exercises, max_exercises)
        state["logs"] += self.apply_model_constraints(constraints, model, vars, phase_components, workout_availability, max_exercises, projected_duration)

        model_with_divided_strain = model.clone()
        state["logs"] += self.app_model_objective(constraints, model, model_with_divided_strain, vars, workout_availability, pc_bounds, min_exercises, max_exercises)

        return {"opt_model": (model, model_with_divided_strain, vars)}

    def solve_model_node(self, state: State, config=None) -> dict:
        self._log_steps("Solving First Step")
        """Solve model and record relaxation attempt results."""
        #return {"solution": "None"}
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
            strain_ratio = duration = working_duration = 0
            schedule = []
            # Each day in the microcycle
            for i in range(len(duration_vars)):
                # Ensure that the phase component is active.
                if(solver.Value(active_exercise_vars[i])):
                    duration_vars_current = solver.Value(duration_vars[i])
                    working_duration_vars_current = solver.Value(working_duration_vars[i])
                    schedule.append((
                        i, 
                        solver.Value(phase_component_vars[i]), 
                        solver.Value(active_exercise_vars[i]), 
                        solver.Value(seconds_per_exercise_vars[i]),                         # Seconds per exercise of the exercise chosen.
                        solver.Value(reps_vars[i]),                                         # Reps of the exercise chosen.
                        solver.Value(sets_vars[i]),                                         # Sets of the exercise chosen.
                        solver.Value(rest_vars[i]) * 5,                                     # Rest of the exercise chosen.
                        solver.Value(volume_vars[i]),                                       # Volume of the exercise chosen.
                        round(solver.Value(density_vars[i]) / 100, 2),                      # Density of the exercise chosen. Scaled down due to scaling up division.
                        round(solver.Value(performance_vars[i]) / 100, 2),                  # Performance of the exercise chosen. Scaled down due to scaling up of intensity AND training weight.
                        duration_vars_current,                                              # Duration of the exercise chosen.
                        working_duration_vars_current,                                      # Working duration of the exercise chosen.
                    ))
                    duration += duration_vars_current
                    working_duration += working_duration_vars_current
                    strain_ratio += duration_vars_current/working_duration_vars_current
            schedule = sorted(schedule, key=lambda x: x[1])
            pc_count = [
                solver.Value(pc_count_var)
                for pc_count_var in pc_count_vars
            ]
            solution = {
                "schedule": schedule,
                "duration": duration,
                "working_duration": working_duration,
                "pc_count": pc_count,
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

    def get_relaxation_formatting_parameters(self, parameters):
        return [
            parameters["availability"],
        ]

    def get_model_formatting_parameters(self, parameters):
        return [
            parameters["phase_components"],
            parameters["projected_duration"],
            parameters["availability"]
        ]

    def format_class_specific_relaxation_history(self, formatted, attempt, workout_availability):
        if workout_availability is not None:
            formatted += f"Workout Length Allowed: {workout_availability // 60} min {workout_availability % 60} sec ({workout_availability} seconds)\n"
        if attempt.duration is not None:
            formatted += f"Total Time Used: {attempt.duration // 60} min {attempt.duration % 60} sec ({attempt.duration} seconds)\n"
        if attempt.working_duration is not None:
            formatted += f"Total Time Worked: {attempt.working_duration // 60} min {attempt.working_duration % 60} sec ({attempt.working_duration} seconds)\n"
        if attempt.strain_ratio is not None:
            formatted += f"Total Strain: {attempt.strain_ratio}\n"
        return formatted

    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("", 5),
            "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
            "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
            "duration": ("Duration", 12),
            "working_duration": ("WDuration", 12),
            "seconds_per_exercise": ("(Sec/Exercise", 16),
            "reps": ("Reps", 14),
            "sets": ("Sets", 10),
            "rest": ("Rest)", 17),
            "volume": ("Volume", 24),
            "density": ("Density", 24),
            "performance": ("Performance", 30)
        }

    def formatted_schedule(self, headers, component_count, phase_component, metrics):
        (active_exercises, seconds_per_exercise, 
         reps_var, sets_var, rest_var, 
         volume_var, density_var, 
         performance_var, duration, working_duration) = metrics

        volume_max = phase_component["volume_max"]
        density_max = phase_component["density_max"] / 100
        performance_max = round(volume_max * density_max * 100) / 100

        # Format line
        line_fields = {
            "number": str(component_count + 1),
            "phase_component": f"{phase_component['name']}",
            "bodypart": phase_component["bodypart_name"],
            "duration": f"({duration} sec",
            "working_duration": f"({working_duration} sec",
            "seconds_per_exercise": f"({seconds_per_exercise} sec",
            "reps": self._format_range(reps_var, phase_component["reps_min"], phase_component["reps_max"]),
            "sets": self._format_range(sets_var, phase_component["sets_min"], phase_component["sets_max"]),
            "rest": self._format_range(rest_var, phase_component["rest_min"] * 5, phase_component["rest_max"] * 5) + ")",
            "volume": f"{volume_var} (>={volume_max})",
            "density": f"{density_var} (>={density_max})",
            "performance": f"{performance_var} (>={performance_max})",
        }

        line = ""
        for field, (_, length) in headers.items():
            line += self._create_formatted_field(field, line_fields[field], length)
        return line + "\n"

    def format_agent_output(self, solution, formatted, schedule, phase_components, projected_duration, workout_availability):
        final_output = []

        phase_component_count = [0] * len(phase_components)

        # Calculate longest string sizes
        longest_sizes = {
            "phase_component": longest_string_size_for_key(phase_components[1:], "name"),
            "bodypart": longest_string_size_for_key(phase_components[1:], "bodypart_name")
        }

        # Create headers
        headers = self._create_header_fields(longest_sizes)
        
        # Create header line
        if log_schedule: 
            formatted += self.formatted_header_line(headers)

        for component_count, (i, phase_component_index, *metrics) in enumerate(schedule):
            phase_component = phase_components[phase_component_index]

            (active_exercises, seconds_per_exercise, 
             reps_var, sets_var, rest_var, 
             volume_var, density_var, 
             performance_var, duration, working_duration) = metrics

            if active_exercises:
                final_output.append({
                    "i": i, 
                    "phase_component_index": phase_component_index, 
                    "phase_component_id": phase_component["phase_component_id"],
                    "bodypart_id": phase_component["bodypart_id"],
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
                if log_schedule:
                    formatted += self.formatted_schedule(headers, component_count, phase_component, metrics)

            else:
                if log_schedule:
                    formatted += (f"| {(component_count + 1):<{2}} ----\n")

        if log_details:
            formatted += f"Phase Component Counts:\n"
            for phase_component_index, phase_component in enumerate(phase_components):
                phase_component_name = f"{phase_component['name']:<{longest_sizes['phase_component']+2}} {phase_component['bodypart_name']:<{longest_sizes['bodypart']+2}}"
                phase_component_range = self._format_range(solution['pc_count'][phase_component_index], phase_component["exercises_per_bodypart_workout_min"], phase_component["exercises_per_bodypart_workout_max"])
                formatted += f"\t{phase_component_name}: {phase_component_range}\n"
            formatted += f"Total Strain: {solution['strain_ratio']}\n"
            formatted += f"Projected Duration: {self._format_duration(projected_duration)}\n"
            formatted += f"Total Duration: {self._format_duration(solution['duration'])}\n"
            formatted += f"Total Work Duration: {self._format_duration(solution['working_duration'])}\n"

        return final_output, formatted

    def run(self):
        graph = self.create_optimization_graph(State)
        result = graph.invoke(self.initial_state)
        return result

def Main(parameters=None, constraints=None):
    agent = ExercisePhaseComponentAgent(parameters, constraints)
    result = agent.run()
    return {"formatted": result["formatted"], "output": result["output"], "solution": result["solution"]}