from langgraph.graph import StateGraph, START, END
from ortools.sat.python import cp_model
from datetime import datetime
from typing import Set, Optional
from dotenv import load_dotenv
from app.agents.constraints import link_entry_and_item, create_optional_intvar, create_duration_var, no_repeated_items, only_use_required_items
from app.agents.base_agent import BaseAgent, BaseAgentState
from app.agents.exercises_phase_components import RelaxationAttempt as RelaxationAttempt2, State, ExerciseComponentsAgent

_ = load_dotenv()

def get_exercises_for_pc(exercises, phase_component):
    exercises_for_pc = [
        i for i, exercise in enumerate(exercises, start=1)
        if (exercise['component_id']==phase_component["component_id"] 
            and exercise['subcomponent_id']==phase_component["subcomponent_id"]
            and ((1 in exercise['bodypart_ids']) or
                 (phase_component["bodypart_id"] in exercise["bodypart_ids"])))]
    if exercises_for_pc == []:
        print(f"{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']} {phase_component['bodypart_name']} has no exercises, if total body, include all.")
        if phase_component["bodypart_id"] == 1:
            exercises_for_pc = [
                i for i, exercise in enumerate(exercises, start=1)
                if (exercise['component_id']==phase_component["component_id"] 
                    and exercise['subcomponent_id']==phase_component["subcomponent_id"])]
    if exercises_for_pc == []:
        print(f"{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']} {phase_component['bodypart_name']} has no exercises, include all.")
        exercises_for_pc = [i for i, _ in enumerate(exercises, start=1)]
    return exercises_for_pc

def get_exercises_for_pc_test(exercises, phase_component):
    print(f"{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']} {phase_component['bodypart_name']}")
    exercises_for_pc = []
    for i, exercise in enumerate(exercises, start=1):
        if (exercise['component_id']==phase_component["component_id"] 
            and exercise['subcomponent_id']==phase_component["subcomponent_id"]
            and ((1 in exercise['bodypart_ids']) or
                 (phase_component["bodypart_id"] in exercise["bodypart_ids"]))):
            print(i, exercise["id"], exercise["name"])
            exercises_for_pc.append(i)
    
    if exercises_for_pc == []:
        print(f"{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']} {phase_component['bodypart_name']} has no exercises, if total body, include all.")
        if phase_component["bodypart_id"] == 1:
            for i, exercise in enumerate(exercises, start=1):
                if (exercise['component_id']==phase_component["component_id"] 
                    and exercise['subcomponent_id']==phase_component["subcomponent_id"]):
                    print(i, exercise["id"], exercise["name"])
                    exercises_for_pc.append(i)
    if exercises_for_pc == []:
        print(f"{phase_component['phase_name']} {phase_component['component_name']} {phase_component['subcomponent_name']} {phase_component['bodypart_name']} has no exercises, include all.")
        for i, exercise in enumerate(exercises, start=1):
            print(i, exercise["id"], exercise["name"])
            exercises_for_pc.append(i)
    print("")
    return exercises_for_pc

class RelaxationAttempt(RelaxationAttempt2):
    def __init__(self, constraints_relaxed: Set[str], result_feasible: bool, 
                 strain_ratio: Optional[int] = None,
                 duration: Optional[int] = None,
                 working_duration: Optional[int] = None,
                 reasoning: Optional[str] = None, expected_impact: Optional[str] = None):
        super().__init__(constraints_relaxed, result_feasible, strain_ratio, duration, working_duration, reasoning, expected_impact)
        self.available_constraints = """
- use_all_phase_components: Forces all phase components to be assigned at least once in a workout.
- base_strain_equals: Forces the amount of base strain to be between the minimum and maximum values allowed for the exercise.
- use_allowed_exercises: Forces the exercise to be one of the exercises allowed for the phase component and bodypart combination.
- no_duplicate_exercises: Forces each exercise to only appear once in the schedule.
- secs_equals: Forces the number of seconds per exercise to be between the minimum and maximum values allowed for the phase component.
- reps_within_min_max: Forces the number of reps to be between the minimum and maximum values allowed for the phase component.
- sets_within_min_max: Forces the number of sets to be between the minimum and maximum values allowed for the phase component.
- rest_within_min_max: Forces the amount of rest to be between the minimum and maximum values allowed for the phase component.
- exercises_per_bodypart_within_min_max: Forces the number of exercises for a phase component to be between the minimum and maximum values allowed.
- minimize_strain: Objective to minimize the amount of strain overall.
"""

class ExerciseAgent(ExerciseComponentsAgent):
    def build_opt_model_node_2(self, state: State, config=None) -> dict:
        print(state["formatted"])

        print("Building Second Step")
        model, phase_component_vars, used_pc_vars, active_exercise_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars = state["opt_model"]

        """Build the optimization model with active constraints."""
        parameters = state["parameters"]
        constraints = state["constraints"]

        exercises = parameters["possible_exercises"]
        exercise_amount = len(exercises)

        phase_components = parameters["phase_components"]

        # Maximum amount of time that the workout may last
        workout_length = min(parameters["availability"], parameters["workout_length"])

        # Define variables =====================================

        # Upper bound on number of exercises (greedy estimation)
        max_exercises = sum((phase_component["exercises_per_bodypart_workout_max"] or 1) for phase_component in phase_components[1:])
        max_seconds_per_exercise = max(phase_component["seconds_per_exercise"] for phase_component in phase_components[1:])
        max_reps = max(phase_component["reps_max"] for phase_component in phase_components[1:])
        max_sets = max(phase_component["sets_max"] for phase_component in phase_components[1:])
        max_rest = max(phase_component["rest_max"] for phase_component in phase_components[1:])
        min_base_strain = min(exercise["base_strain"] for exercise in exercises[1:])
        max_base_strain = max(exercise["base_strain"] for exercise in exercises[1:])
        max_strain_scaled = ((max_seconds_per_exercise * (10 + max_base_strain) * max_reps) + (10 *max_rest * 5)) * max_sets

        used_exercise_vars = []
        base_strain_vars = []
        exercise_vars = []

        for i in range(max_exercises):
            is_exercise_active_var = active_exercise_vars[i]

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

            # Create an optional entry for the seconds per exercise variables.
            model, base_strain_var_entry = create_optional_intvar(
                model=model, activator=is_exercise_active_var,
                min_if_active=min_base_strain,
                max_if_active=max_base_strain,
                name_of_entry_var=f'base_strain_{i}')

            used_exercise_vars.append(used_exercise_vars_entry)
            base_strain_vars.append(base_strain_var_entry)
            exercise_vars.append(exercise_var_entry)

        # Links the exercise variables and the exercises that can exist via the used exercises variables.
        model = link_entry_and_item(model = model, 
                                    items = exercises, 
                                    entry_vars = exercise_vars, 
                                    number_of_entries = max_exercises, 
                                    used_vars = used_exercise_vars)

        # Apply active constraints ======================================
        state["logs"] += "\nBuilding model with constraints:\n"

        # Constraint: Use only allowed exercises
        if constraints["use_allowed_exercises"]:
            for phase_component_index, phase_component in enumerate(phase_components[1:], start=1):
                exercises_for_pc = get_exercises_for_pc(exercises[1:], phase_component)
                exercises_for_pc.insert(0, 0)
                conditions = [row[phase_component_index] for row in used_pc_vars]

                model = only_use_required_items(model = model, 
                                                required_items = exercises_for_pc, 
                                                entry_vars = exercise_vars, 
                                                active_entry_vars = active_exercise_vars, 
                                                conditions = conditions)
            state["logs"] += "- Only use allowed exercises applied.\n"

        # Constraint: Ensure each exercise only appears once in the schedule
        if constraints["no_duplicate_exercises"]:
            required_phase_components = list(range(1, len(exercises)))
            model = no_repeated_items(model = model, 
                                      required_items = required_phase_components, 
                                      used_vars = used_exercise_vars)
            state["logs"] += "- No duplicate exercises constraint applied.\n"

        # Objective: Maximize total duration of microcycle
        if constraints["minimize_strain"]:
            # List of contributions to goal time.
            strain_terms = []

            # Creates strain_time, which will hold the total strain over the workout.
            strain_time = model.NewIntVar(0, max_exercises * workout_length, 'strain_time')
            for i, values_for_exercise in enumerate(zip(active_exercise_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars)):
                (
                    active_exercise_var, 
                    base_strain_var,
                    seconds_per_exercise_var, 
                    reps_var, 
                    sets_var, 
                    rest_var
                ) = values_for_exercise
                # Create the entry for phase component's duration
                # total_working_duration = (seconds_per_exercise*(1+.1*basestrain)* rep_count) * set_count
                #working_duration_var = model.NewIntVar(0, workout_length, f'working_duration_{i}')
                non_zero_working_duration_var = model.NewIntVar(1, 10 * workout_length, f'working_duration_{i}')
                working_duration_is_0 = model.NewBoolVar(f'working_duration_{i}_is_0')

                model, duration_var = create_duration_var(model=model, 
                                                          i=i, 
                                                          workout_length=max_strain_scaled, 
                                                          seconds_per_exercise=seconds_per_exercise_var, 
                                                          reps=reps_var, 
                                                          sets=sets_var, 
                                                          rest=rest_var,
                                                          base_strain=base_strain_var,
                                                          name="base_",
                                                          scaled=10)

                model, working_duration_var = create_duration_var(model=model, 
                                                          i=i, 
                                                          workout_length=max_strain_scaled, 
                                                          seconds_per_exercise=seconds_per_exercise_var, 
                                                          reps=reps_var, 
                                                          sets=sets_var, 
                                                          rest=0,
                                                          base_strain=base_strain_var,
                                                          name="working_",
                                                          scaled=10)

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

        return {"opt_model": (model, exercise_vars, phase_component_vars, active_exercise_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars)}

    def solve_model_node_2(self, state: State, config=None) -> dict:
        print("Solving Second Step")
        """Solve model and record relaxation attempt results."""
        #return {"solution": "None"}
        model, exercise_vars, phase_component_vars, active_exercise_vars, base_strain_vars, seconds_per_exercise_vars, reps_vars, sets_vars, rest_vars, duration_vars = state["opt_model"]

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
                if(solver.Value(active_exercise_vars[i])):
                    seconds_per_exercise_current = solver.Value(seconds_per_exercise_vars[i])
                    reps_vars_current = solver.Value(reps_vars[i])
                    sets_vars_current = solver.Value(sets_vars[i])
                    duration_vars_current = solver.Value(duration_vars[i])
                    working_duration_vars_current = (seconds_per_exercise_current * reps_vars_current * sets_vars_current)
                    schedule.append((
                        i, 
                        solver.Value(exercise_vars[i]), 
                        solver.Value(phase_component_vars[i]), 
                        solver.Value(active_exercise_vars[i]), 
                        solver.Value(base_strain_vars[i]), 
                        seconds_per_exercise_current, 
                        reps_vars_current, 
                        sets_vars_current, 
                        solver.Value(rest_vars[i]) * 5, 
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
        solution = state["solution"]

        parameters = state["parameters"]

        exercises, phase_components, projected_duration = parameters["possible_exercises"], parameters["phase_components"], parameters["projected_duration"]
        workout_length = min(parameters["availability"], parameters["workout_length"])

        longest_subcomponent_string_size = len(max(phase_components[1:], key=lambda d:len(d["name"]))["name"])
        longest_bodypart_string_size = len(max(phase_components[1:], key=lambda d:len(d["bodypart_name"]))["bodypart_name"])

        longest_pc_string_size = longest_subcomponent_string_size + longest_bodypart_string_size
        longest_exercise_string_size = len(max(exercises[1:], key=lambda d:len(d["name"]))["name"])

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
                phase_component = phase_components[phase_component_index]

                phase_component_name = phase_component["name"] + " " + phase_component["bodypart_name"] 

                #duration = (bodypart_var * (seconds_per_exercise * reps_var + rest_var) * sets_var)

                if active_exercises:
                    final_output.append({
                        "i": i, 
                        "exercise_index": exercise_index,
                        "exercise_id": exercise["id"],
                        "phase_component_index": phase_component_index, 
                        "phase_component_id": phase_component["phase_component_id"],
                        "bodypart_id": phase_component["bodypart_id"],
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

                    formatted_exercise = f"{exercise["name"]:<{longest_exercise_string_size+3}}"
                    formatted_phase_component = f"{phase_component_name:<{longest_pc_string_size+3}}"

                    formatted_duration = f"Duration: {duration // 60} min {duration % 60} sec ({duration} seconds)"
                    formatted_base_strain = f"Base Strain {base_strain:<{3}}\t"
                    formatted_seconds_per_exercises = f"Sec/Exercise {seconds_per_exercise:<{5}}"
                    formatted_reps = f"Reps {reps_var} ({phase_component["reps_min"]}-{phase_component["reps_max"]})"
                    formatted_sets = f"Sets {sets_var} ({phase_component["sets_min"]}-{phase_component["sets_max"]})"
                    formatted_rest = f"Rest {rest_var} ({phase_component["rest_min"] * 5}-{phase_component["rest_max"] * 5})"

                    formatted += (f"Exercise {(component_count + 1):<{2}}: {formatted_exercise}{formatted_base_strain}{formatted_phase_component}{formatted_duration:<{45}}({formatted_seconds_per_exercises}{formatted_reps:<{20}}{formatted_sets:<{20}}{formatted_rest:<{6}})\n")
                else:
                    formatted += (f"Exercise {(component_count + 1):<{2}} ----\n")

            formatted += f"Phase Component Counts:\n"
            for phase_component_index, phase_component_number in enumerate(phase_component_count):
                phase_component = phase_components[phase_component_index]
                formatted += f"\t{phase_component["name"] + " " + phase_component["bodypart_name"]:<{longest_pc_string_size+3}}: {phase_component_number} ({phase_component["exercises_per_bodypart_workout_min"]}-{phase_component["exercises_per_bodypart_workout_max"]})\n"
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


    def create_optimization_graph(self, state_class):
        builder = StateGraph(state_class)

        # Add common nodes
        builder.add_node("setup", self.setup_params_node)
        builder.add_node("build_1", self.build_opt_model_node)
        builder.add_node("solve_1", self.solve_model_node)
        builder.add_node("analyze", self.analyze_infeasibility_node)
        builder.add_node("format_1", self.format_solution_node)

        builder.add_node("build_2", self.build_opt_model_node_2)
        builder.add_node("solve_2", self.solve_model_node_2)
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
                "format": "format_1"
            }
        )

        builder.add_edge("format_1", "build_2")
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
