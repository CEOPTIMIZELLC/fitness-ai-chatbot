from ortools.sat.python import cp_model
from datetime import datetime
from typing import Set, Optional
from dotenv import load_dotenv
from app.agents.constraints import (
    create_optional_intvar, 
    create_spread_intvar, 
    day_duration_within_availability, 
    use_workout_required_components, 
    use_all_required_items, 
    frequency_within_min_max, 
    consecutive_bodyparts_for_component)

from app.agents.base_agent import BaseAgent, BaseAgentState

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

def declare_model_vars(model, phase_components, weekday_availability, workout_length, microcycle_weekdays):
    workout_availability = []
    active_workday_vars = []
    active_phase_components = []
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
        
        active_phase_components_for_day = []
        duration_vars_for_day = []

        # Each phase component in the day.
        for index_for_phase_component, phase_component in enumerate(phase_components):
            is_phase_active_var = (model.NewBoolVar(
                f'phase_component_{index_for_phase_component}_active_on_day_{index_for_day}'))

            # Create the entry for phase component's duration
            # phase duration = number_of_bodypart_exercises * (seconds_per_exercise * rep_count + rest_time) * set_count
            duration_var_entry = create_optional_intvar(
                model=model, activator=is_phase_active_var,
                min_if_active=phase_component["duration_min"],
                max_if_active=min(phase_component["duration_max"], workout_length),
                name_of_entry_var=f'phase_component_{index_for_phase_component}_duration_on_day_{index_for_day}')

            active_phase_components_for_day.append(is_phase_active_var)
            duration_vars_for_day.append(duration_var_entry)
        
        # Append the new row to the corresponding 2D arrays.
        active_phase_components.append(active_phase_components_for_day)
        duration_vars.append(duration_vars_for_day)
    return (workout_availability, active_workday_vars, active_phase_components, duration_vars)


class State(BaseAgentState):
    parameter_input: dict

class PhaseComponentAgent(BaseAgent):
    def __init__(self, parameters={}, constraints={}):
        super().__init__()
        self.initial_state["parameter_input"]={
            "parameters": parameters, 
            "constraints": constraints}
        self.available_constraints = """
- day_duration_within_availability: Prevents workout from exceeding the time allowed for that given day.
- day_duration_within_workout_length: Prevents workout from exceeding the length allowed for a workout.
- use_workout_required_components: Forces all phase components required for a workout to be assigned in every workout.
- use_microcycle_required_components: Forces all phase components required for a microcycle to be assigned at lease once in the microcycle.
- frequency_within_min_max: Forces each phase component that does occur to occur between the minimum and maximum values allowed.
- consecutive_bodyparts_for_component: Forces phase components of the same component and subcomponent type to occur simultaneously on a workout where any is assigned.
- minimize_duration_delta: Secondary objective to minimize the amount of spread of phase component durations.
- maximize_exercise_time: Objective to maximize the amount of time spent overall.
"""

    def setup_params_node(self, state: State, config=None) -> dict:
        """Initialize optimization parameters and constraints."""

        parameter_input = state.get("parameter_input", {})

        parameters = {
            "weekday_availability": [
                {"id": 0, "name": "Monday", "availability": 6 * 60 * 60},
                {"id": 1, "name": "Tuesday", "availability": 3 * 60 * 60},
                {"id": 2, "name": "Wednesday", "availability": 2 * 60 * 60},
                {"id": 3, "name": "Thursday", "availability": 35 * 60},
                {"id": 4, "name": "Friday", "availability": 10 * 60 * 60},
                {"id": 5, "name": "Saturday", "availability": 2 * 60 * 60},
                {"id": 6, "name": "Sunday", "availability": 0 * 60 * 60},
            ],
            "microcycle_weekdays": [0, 1, 2, 3, 4, 5, 6],
            "workout_length": 50 * 60,
            "phase_components": []
        }

        # Define all constraints with their active status
        constraints = {
            "day_duration_within_availability": True,       # The time of a workout won't exceed the time allowed for that given day.
            "day_duration_within_workout_length": True,     # The time of a workout won't exceed the length allowed for a workout.
            "use_workout_required_components": True,        # Include phase components that are required in every workout at least once.
            "use_microcycle_required_components": True,     # Include phase components that are required in every microcycle at least once.
            "frequency_within_min_max": True,               # The number of times that a phase component may be used in a microcycle is within number allowed.
            "consecutive_bodyparts_for_component": False,    # Every bodypart division must be done consecutively for a phase component.
            "minimize_duration_delta": True,                # Minimize the amount of spread across the duration of phase component over the microcycle.
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

    def build_opt_model_node(self, state: State, config=None) -> dict:
        """Build the optimization model with active constraints."""
        parameters = state["parameters"]
        constraints = state["constraints"]
        model = cp_model.CpModel()

        phase_components = parameters["phase_components"]
        weekday_availability = parameters["weekday_availability"]
        workout_length = parameters["workout_length"]
        microcycle_weekdays = parameters["microcycle_weekdays"]

        (workout_availability, active_workday_vars, active_phase_components, duration_vars) = declare_model_vars(model, phase_components, weekday_availability, workout_length, microcycle_weekdays)

        # Apply active constraints ======================================
        state["logs"] += "\nBuilding model with constraints:\n"

        # Constraint: The duration of a day may only be a number of hours between the allowed time for that day.
        if constraints["day_duration_within_availability"]:
            day_duration_within_availability(model=model, 
                                             duration_vars=duration_vars, 
                                             availability=workout_availability)
            state["logs"] += "- Sum of phase component duration within maximum allowed time for a day.\n"

        # Ensure that the duration doesn't exceed the maximum allowed time for a workout.
        #model.Add(duration_var_entry <= workout_length)
        # Constraint: The duration of a day may only be a number of hours less than the allowed time for a workout.
        if constraints["day_duration_within_workout_length"]:
            day_duration_within_availability(model=model, 
                                             duration_vars=duration_vars, 
                                             availability=[workout_length] * len(duration_vars))
            state["logs"] += "- Sum of phase component duration within maximum allowed time for a workout.\n"


        # Constraint: Force all phase components required in every workout to be included at least once.
        if constraints["use_workout_required_components"]:
            # Retrieve the indexes of all components that are required in all workouts.
            required_phase_components = [i for i, phase_component in enumerate(phase_components) if phase_component["required_every_workout"]]
            use_workout_required_components(model=model, 
                                            required_items=required_phase_components, 
                                            used_vars=active_phase_components, 
                                            active_entry_vars=active_workday_vars)
            state["logs"] += "- All phase components required every workout will be included in every workout applied.\n"

        # Constraint: Force all phase components required in every microcycle to be included at least once.
        if constraints["use_microcycle_required_components"]:
            # Retrieve the indexes of all components that are required at least once in a microcycle.
            required_phase_components = [i for i, phase_component in enumerate(phase_components) if phase_component["required_within_microcycle"] == "always"]
            use_all_required_items(model=model, 
                                   required_items=required_phase_components, 
                                   used_vars=active_phase_components)
            state["logs"] += "- All phase components required every microcycle will be included in every microcycle applied.\n"


        # Constraint: Every bodypart division must be done consecutively for a phase component.
        if constraints["consecutive_bodyparts_for_component"]:
            consecutive_bodyparts_for_component(model=model, 
                                                phase_components=phase_components, 
                                                active_phase_components=active_phase_components)
            state["logs"] += "- Bodypart division for components are done consecutively activated.\n"


        # Constraint: # Force number of occurrences of a phase component within in a microcycle to be within number allowed.
        if constraints["frequency_within_min_max"]:
            frequency_within_min_max(model=model, 
                                     phase_components=phase_components, 
                                     active_phase_components=active_phase_components,
                                     minimum_key="frequency_per_microcycle_min",
                                     maximum_key="frequency_per_microcycle_max")
            state["logs"] += "- All phase components occuring within microcycle will occur the allowed number of times applied.\n"

        duration_spread_var = None
        # Secondary Objective: Minimize the spread of duration.
        if constraints["minimize_duration_delta"]:
            duration_spread_var = create_spread_intvar(model=model, 
                                                       entry_vars=duration_vars, 
                                                       entry_var_name="duration_var", 
                                                       active_entry_vars=active_phase_components, 
                                                       max_value_allowed=max(workout_availability))
            state["logs"] += "- Minimizing spread across duration applied.\n"

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
            total_duration_to_maximize = 1000 * sum(total_set_duration_for_day)

            # Spread reduction.
            '''if duration_spread_var != None:
                total_duration_to_maximize -= 1 * duration_spread_var'''

            # Maximize the total
            model.Maximize(total_duration_to_maximize)
            state["logs"] += "- Maximizing time used in microcycle.\n"

        return {"opt_model": (model, workout_availability, active_phase_components, duration_vars, duration_spread_var, total_duration_to_maximize)}

    def solve_model_node(self, state: State, config=None) -> dict:
        """Solve model and record relaxation attempt results."""
        model, workout_availability, active_phase_components, duration_vars, duration_spread_var, total_duration_to_maximize = state["opt_model"]

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 12

        # solver.parameters.log_search_progress = True
        status = solver.Solve(model)

        # If the duration spread should be minimized, then ensure the final duration is the same, with the new goal of minimizing the spread.
        if duration_spread_var != None:
            model.Add((total_duration_to_maximize == solver.Value(total_duration_to_maximize)))
            model.Minimize(duration_spread_var)
            status = solver.Solve(model)
        
        state["logs"] += f"\nSolver status: {status}\n"
        state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            microcycle_duration = 0
            schedule = []

            # Each day in the microcycle
            for index_for_day, values_for_day in enumerate(zip(workout_availability, active_phase_components, duration_vars)):
                workout_availability_for_day, active_phase_components_for_day, duration_vars_for_day = values_for_day

                # Each phase used in the day.
                for index_for_phase_component, values_for_phase_component in enumerate(zip(active_phase_components_for_day, duration_vars_for_day)):
                    active_phase_components_for_phase_component, duration_vars_for_phase_component = values_for_phase_component

                    # Ensure that the phase component is active.
                    if(solver.Value(active_phase_components_for_phase_component)):
                        duration_vars_current = solver.Value(duration_vars_for_phase_component)

                        schedule.append((
                            index_for_phase_component, index_for_day, 
                            solver.Value(active_phase_components_for_phase_component), 
                            duration_vars_current
                        ))
                        microcycle_duration += duration_vars_current
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

    def format_solution_node(self, state: State, config=None) -> dict:
        """Format the optimization results."""
        solution = state["solution"]

        parameters = state["parameters"]

        phase_components = parameters["phase_components"]
        weekday_availability = parameters["weekday_availability"]
        workout_length = parameters["workout_length"]
        microcycle_weekdays = parameters["microcycle_weekdays"]

        longest_subcomponent_string_size = len(max(phase_components, key=lambda d:len(d["name"]))["name"])
        longest_bodypart_string_size = len(max(phase_components, key=lambda d:len(d["bodypart"]))["bodypart"])

        longest_string_size = longest_subcomponent_string_size + longest_bodypart_string_size

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

            for component_count, (phase_component_index, workday_index, active_phase_components, duration_var) in enumerate(schedule):

                phase_component = phase_components[phase_component_index]
                phase_component_id = phase_component["id"]
                bodypart_id = phase_component["bodypart_id"]
                phase_component_name = phase_component["name"] + " " + phase_component["bodypart"] 

                day_duration = duration_var

                if active_phase_components:
                    final_output.append({
                        "workday_index": workday_index, 
                        "phase_component_index": phase_component_index, 
                        "phase_component_id": phase_component_id,
                        "bodypart_id": bodypart_id,
                        "active_phase_components": active_phase_components, 
                        "duration_var": duration_var
                    })

                    current_weekday = microcycle_weekdays[workday_index]

                    if not used_days[workday_index]["used"]:
                        formatted += f"\nDay {workday_index + 1} {weekday_availability[current_weekday]["name"]:<{10}} Availability of {used_days[workday_index]["availability"]  // 60} min {used_days[workday_index]["availability"]  % 60} sec ({used_days[workday_index]["availability"]} seconds)\n"
                        used_days[workday_index]["used"] = True

                    # Count the number of occurrences of each phase component
                    phase_component_count[phase_component_index] += 1

                    formatted_duration = f"Duration: {(day_duration // 60):<{3}} min {(day_duration % 60):<{3}} sec\t"
                    formatted_duration_sec = f"{day_duration:<{5}} seconds ({phase_component["duration_min"]}-{phase_component["duration_max"]})"

                    formatted += (f"\tComp {(component_count + 1):<{3}}: {phase_component_name:<{longest_string_size+3}} {formatted_duration} {formatted_duration_sec}\n")
                else:
                    formatted += (f"Day {workday_index + 1}; Comp {component_count + 1}: \t{phase_component_name:<{longest_string_size+3}} ----\n")

            formatted += f"Phase Component Counts:\n"
            for phase_component_index, phase_component_number in enumerate(phase_component_count):
                phase_component = phase_components[phase_component_index]
                formatted += f"\t{phase_component["name"] + " " + phase_component["bodypart"]:<{longest_string_size+3}}: {phase_component_number} ({phase_component["frequency_per_microcycle_min"]} - {phase_component["frequency_per_microcycle_max"]})\n"
            formatted += f"Total Time Used: {solution['microcycle_duration']  // 60} min {solution['microcycle_duration']  % 60} sec ({solution['microcycle_duration']}) seconds\n"
            formatted += f"Total Time Allowed: {workout_time  // 60} min {workout_time  % 60} sec ({workout_time} seconds)\n"
            formatted += f"Workout Length Allowed: {workout_length  // 60} min {workout_length  % 60} sec ({workout_length} seconds)\n"

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
    agent = PhaseComponentAgent(parameters, constraints)
    result = agent.run()
    return {"formatted": result["formatted"], "output": result["output"], "solution": result["solution"]}

if __name__ == "__main__":
    result = Main()
    print(result["formatted"])
