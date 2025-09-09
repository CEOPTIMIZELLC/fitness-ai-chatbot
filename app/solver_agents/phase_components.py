from config import ortools_solver_time_in_seconds, SchedulerLoggingConfig
from logging_config import LogSolver
from ortools.sat.python import cp_model
from typing import Set, Optional
from dotenv import load_dotenv
from app.solver_agents.constraints import (
    create_optional_intvar, 
    create_spread_intvar, 
    day_duration_within_availability, 
    use_workout_required_components, 
    use_all_required_items,
    ensure_all_vars_equal, 
    frequency_within_min_max, 
    consecutive_bodyparts_for_component)

from app.solver_agents.base_agent import BaseRelaxationAttempt, BaseAgent, BaseAgentState
from app.utils.longest_string import longest_string_size_for_key

_ = load_dotenv()

available_constraints = """
- day_duration_within_availability: Prevents workout from exceeding the time allowed for that given day.
- use_workout_required_components: Forces all phase components required for a workout to be assigned in every workout.
- only_use_required_components: Forces only required phase components to be assigned.
- use_microcycle_required_components: Forces all phase components required for a microcycle to be assigned at lease once in the microcycle.
- frequency_within_min_max: Forces each phase component that does occur to occur between the minimum and maximum values allowed.
- consecutive_bodyparts_for_component: Forces phase components of the same component and subcomponent type to occur simultaneously on a workout where any is assigned.
- resistances_have_equal_counts: Forces all phase components of different subcomponent types to have the same quantity if they are resistance components in a day.
- minimize_duration_delta: Secondary objective to minimize the amount of spread of phase component durations.
- maximize_exercise_time: Objective to maximize the amount of time spent overall.
"""

def user_workout_time(weekday_availability, microcycle_weekdays):
    used_days = []

    # Total time the user has to workout.
    workout_time = 0
    for day in microcycle_weekdays:
        workout_availability = weekday_availability[day]["availability"]
        used_days.append({"used": False, "availability": workout_availability})
        workout_time += workout_availability
    return used_days, workout_time

class RelaxationAttempt(BaseRelaxationAttempt):
    def __init__(self, 
                 constraints_relaxed: Set[str], 
                 result_feasible: bool, 
                 microcycle_duration: Optional[int] = None,
                 reasoning: Optional[str] = None, 
                 expected_impact: Optional[str] = None):
        super().__init__(constraints_relaxed, result_feasible, reasoning, expected_impact)
        self.microcycle_duration = microcycle_duration


class State(BaseAgentState):
    parameter_input: dict

class PhaseComponentAgent(BaseAgent):
    schedule_title = "Phase Component Subagent"
    available_constraints = available_constraints

    def __init__(self, parameters={}, constraints={}):
        super().__init__()
        self.initial_state["parameter_input"]={
            "parameters": parameters, 
            "constraints": constraints}

    def setup_params_node(self, state: State, config=None) -> dict:
        LogSolver.agent_steps(f"{self.schedule_title}: Setting up the parameters and configurations.")
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
            "phase_components": []
        }

        # Define all constraints with their active status
        constraints = {
            "day_duration_within_availability": True,       # The time of a workout won't exceed the time allowed for that given day.
            "use_workout_required_components": True,        # Include phase components that are required in every workout at least once.
            "only_use_required_components": True,           # Only required phase components are included.
            "use_microcycle_required_components": True,     # Include phase components that are required in every microcycle at least once.
            "frequency_within_min_max": True,               # The number of times that a phase component may be used in a microcycle is within number allowed.
            "consecutive_bodyparts_for_component": False,    # Every bodypart division must be done consecutively for a phase component.
            "resistances_have_equal_counts": True,          # Forces all phase components of different subcomponent types to have the same quantity if they are resistance components in the same day.
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
    
    def create_model_vars(self, model, phase_components, workout_availability, microcycle_weekdays):
        LogSolver.agent_steps(f"{self.schedule_title}: Create the model variables for the solver.")

        # Define variables =====================================
        agent_vars = {}

        # Boolean variables indicating whether exercise i is active.
        agent_vars["active_workday"] = [
            model.NewBoolVar(f'day_{index_for_day}_is_active') 
            for index_for_day in range(len(microcycle_weekdays))]

        # Ensure that the workday is considered inactive if it is 0 hours long.
        for workout_availability_for_day, is_active_workday in zip(workout_availability, agent_vars["active_workday"]):
            if workout_availability_for_day > 0:
                model.Add(is_active_workday == True)
            else:
                model.Add(is_active_workday == False)

        # Boolean variables indicating whether phase component j is active on day i.
        agent_vars["active_phase_components"] = [[
            model.NewBoolVar(f'phase_component_{index_for_phase_component}_is_active_on_day_{index_for_day}')
            for index_for_phase_component in range(len(phase_components))]
            for index_for_day in range(len(microcycle_weekdays))]

        # Create the entry for phase component's count
        # phase duration = number_of_bodypart_exercises * (seconds_per_exercise * rep_count + rest_time) * set_count
        agent_vars["exercises_per_bodypart"] = [[
            create_optional_intvar(
                model=model, 
                activator = agent_vars["active_phase_components"][index_for_day][index_for_phase_component],
                min_if_active = phase_components[index_for_phase_component]["exercises_per_bodypart_workout_min"],
                max_if_active = phase_components[index_for_phase_component]["exercises_per_bodypart_workout_max"],
                name_of_entry_var = f'phase_component_{index_for_phase_component}_number_of_exercises_on_day_{index_for_day}')
            for index_for_phase_component in range(len(phase_components))]
            for index_for_day in range(len(microcycle_weekdays))]

        # Create the entry for phase component's duration
        # phase duration = number_of_bodypart_exercises * (seconds_per_exercise * rep_count + rest_time) * set_count
        agent_vars["partial_duration"] = [[
            create_optional_intvar(
                model=model, 
                activator = agent_vars["active_phase_components"][index_for_day][index_for_phase_component],
                min_if_active = phase_components[index_for_phase_component]["duration_min"],
                max_if_active = phase_components[index_for_phase_component]["duration_max"],
                name_of_entry_var = f'phase_component_{index_for_phase_component}_partial_duration_on_day_{index_for_day}')
            for index_for_phase_component in range(len(phase_components))]
            for index_for_day in range(len(microcycle_weekdays))]

        # Create the entry for phase component's duration
        # phase duration = number_of_bodypart_exercises * (seconds_per_exercise * rep_count + rest_time) * set_count
        agent_vars["duration"] = [[
            model.NewIntVar(0, len(phase_components) * phase_components[index_for_phase_component]["duration_max"], f'phase_component_{index_for_phase_component}_duration_on_day_{index_for_day}') 
            for index_for_phase_component in range(len(phase_components))]
            for index_for_day in range(len(microcycle_weekdays))]

        # Add relationship between exercises per bodypart and the partial duration.
        for exs_for_day, partial_durations_for_day, durations_for_day in zip(agent_vars["exercises_per_bodypart"], agent_vars["partial_duration"], agent_vars["duration"]):
            for ex_for_pc, partial_duration_for_pc, duration_for_pc in zip(exs_for_day, partial_durations_for_day, durations_for_day):
                model.AddMultiplicationEquality(duration_for_pc, [ex_for_pc, partial_duration_for_pc])
        return agent_vars


    def apply_model_constraints(self, constraints, model, agent_vars, phase_components, workout_availability):
        LogSolver.agent_steps(f"{self.schedule_title}: Apply model constraints.")

        # Apply active constraints ======================================
        logs = "\nBuilding model with constraints:\n"

        # Constraint: The duration of a day may only be a number of hours between the allowed time for that day.
        if constraints["day_duration_within_availability"]:
            day_duration_within_availability(model=model, 
                                             duration_vars=agent_vars["duration"], 
                                             availability=workout_availability)
            logs += "- Sum of phase component duration within maximum allowed time for a day.\n"

        # Constraint: Force all phase components required in every workout to be included at least once.
        if constraints["use_workout_required_components"]:
            # Retrieve the indexes of all components that are required in all workouts.
            required_phase_components = [i for i, phase_component in enumerate(phase_components) if phase_component["required_every_workout"]]
            use_workout_required_components(model=model, 
                                            required_items=required_phase_components, 
                                            used_vars=agent_vars["active_phase_components"], 
                                            active_entry_vars=agent_vars["active_workday"])
            logs += "- All phase components required every workout will be included in every workout applied.\n"

        # Constraint: Only use required phase components
        if constraints["only_use_required_components"]:
            # Retrieves the index of all required phases.
            not_required_phase_components = [i for i, phase_component in enumerate(phase_components) if phase_component["required_within_microcycle"] != "always"]
            for item_index in not_required_phase_components:
                conditions = [row[item_index].Not() for row in agent_vars["active_phase_components"]]
                model.AddBoolAnd(conditions)
            logs += "- Only use required phases components applied.\n"

        # Constraint: Force all phase components required in every microcycle to be included at least once.
        if constraints["use_microcycle_required_components"]:
            # Retrieve the indexes of all components that are required at least once in a microcycle.
            required_phase_components = [i for i, phase_component in enumerate(phase_components) if phase_component["required_within_microcycle"] == "always"]
            use_all_required_items(model=model, 
                                   required_items=required_phase_components, 
                                   used_vars=agent_vars["active_phase_components"])
            logs += "- All phase components required every microcycle will be included in every microcycle applied.\n"

        # Constraint: Every bodypart division must be done consecutively for a phase component.
        if constraints["consecutive_bodyparts_for_component"]:
            consecutive_bodyparts_for_component(model=model, 
                                                phase_components=phase_components, 
                                                active_phase_components=agent_vars["active_phase_components"])
            logs += "- Bodypart division for components are done consecutively activated.\n"


        # Constraint: All resistances of different subcomponents will have the same number.
        if constraints["resistances_have_equal_counts"]:
            resistance_phase_components = {}
            for i, phase_component in enumerate(phase_components):
                if phase_component["component_name"].lower() == "resistance":
                    resistance_phase_components.setdefault(phase_component["bodypart_id"],[]).append(i)
            for active_phase_components_for_day in agent_vars["active_phase_components"]:
                for _, value in resistance_phase_components.items():
                    ensure_all_vars_equal(model, [active_phase_components_for_day[i] for i in value])
            logs += "- All resistances of different subcomponents will have the same number activated.\n"

        # Constraint: # Force number of occurrences of a phase component within in a microcycle to be within number allowed.
        if constraints["frequency_within_min_max"]:
            frequency_within_min_max(model=model, 
                                     phase_components=phase_components, 
                                     active_phase_components=agent_vars["active_phase_components"],
                                     minimum_key="frequency_per_microcycle_min",
                                     maximum_key="frequency_per_microcycle_max")
            logs += "- All phase components occuring within microcycle will occur the allowed number of times applied.\n"

        return logs

    def apply_model_objective(self, constraints, model, agent_vars, workout_availability):
        LogSolver.agent_steps(f"{self.schedule_title}: Apply model objective.")

        logs = ""
        duration_spread_var = None
        # Secondary Objective: Minimize the spread of duration.
        if constraints["minimize_duration_delta"]:
            duration_spread_var = create_spread_intvar(model=model, 
                                                       entry_vars=agent_vars["duration"], 
                                                       entry_var_name="duration_var", 
                                                       active_entry_vars=agent_vars["active_phase_components"], 
                                                       max_value_allowed=max(workout_availability))
            logs += "- Minimizing spread across duration applied.\n"

        # Objective: Maximize total duration of microcycle
        if constraints["maximize_exercise_time"]:
            # List of contributions to goal time.
            total_set_duration_for_day = []

            # Each day
            for duration_vars_for_day in agent_vars["duration"]:
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
            logs += "- Maximizing time used in microcycle.\n"
        return logs, duration_spread_var, total_duration_to_maximize


    def build_opt_model_node(self, state: State, config=None) -> dict:
        LogSolver.agent_steps(f"{self.schedule_title}: Building Model")

        """Build the optimization model with active constraints."""
        parameters = state["parameters"]
        constraints = state["constraints"]
        model = cp_model.CpModel()

        phase_components = parameters["phase_components"]
        weekday_availability = parameters["weekday_availability"]
        microcycle_weekdays = parameters["microcycle_weekdays"]

        workout_availability = [weekday_availability[day]["availability"] for day in microcycle_weekdays]

        agent_vars = self.create_model_vars(model, phase_components, workout_availability, microcycle_weekdays)
        state["logs"] += self.apply_model_constraints(constraints, model, agent_vars, phase_components, workout_availability)
        logs, duration_spread_var, total_duration_to_maximize = self.apply_model_objective(constraints, model, agent_vars, workout_availability)
        state["logs"] += logs

        return {"opt_model": (model, workout_availability, agent_vars, duration_spread_var, total_duration_to_maximize)}

    def solve_model_node(self, state: State, config=None) -> dict:
        LogSolver.agent_steps(f"{self.schedule_title}: Solving Model")

        """Solve model and record relaxation attempt results."""
        model, workout_availability, agent_vars, duration_spread_var, total_duration_to_maximize = state["opt_model"]
        active_phase_components, exercises_per_bodypart_vars, partial_duration_vars, duration_vars = agent_vars["active_phase_components"], agent_vars["exercises_per_bodypart"], agent_vars["partial_duration"], agent_vars["duration"]

        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 12
        solver.parameters.max_time_in_seconds = ortools_solver_time_in_seconds

        # solver.parameters.log_search_progress = True
        status = self._solve_and_time_solver(solver, model)

        # If the duration spread should be minimized, then ensure the final duration is the same, with the new goal of minimizing the spread.
        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL) and duration_spread_var != None:
            model.Add((total_duration_to_maximize == solver.Value(total_duration_to_maximize)))
            model.Minimize(duration_spread_var)
            status = solver.Solve(model)

        state["logs"] += f"\nSolver status: {status}\n"
        state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            microcycle_duration = 0
            schedule = []

            # Each day in the microcycle
            for index_for_day, values_for_day in enumerate(zip(workout_availability, active_phase_components, exercises_per_bodypart_vars, partial_duration_vars, duration_vars)):
                workout_availability_for_day, active_phase_components_for_day, exercises_per_bodypart_vars_for_day, partial_duration_vars_for_day, duration_vars_for_day = values_for_day

                # Each phase used in the day.
                for index_for_phase_component, values_for_phase_component in enumerate(zip(active_phase_components_for_day, exercises_per_bodypart_vars_for_day, partial_duration_vars_for_day, duration_vars_for_day)):
                    active_phase_components_for_phase_component, exercises_per_bodypart_vars_for_phase_component, partial_duration_vars_for_phase_component, duration_vars_for_phase_component = values_for_phase_component

                    # Ensure that the phase component is active.
                    if(solver.Value(active_phase_components_for_phase_component)):
                        duration_vars_current = solver.Value(duration_vars_for_phase_component)

                        schedule.append((
                            index_for_phase_component, index_for_day, 
                            solver.Value(active_phase_components_for_phase_component), 
                            solver.Value(exercises_per_bodypart_vars_for_phase_component), 
                            solver.Value(partial_duration_vars_for_phase_component), 
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

    def get_relaxation_formatting_parameters(self, parameters):
        weekday_availability = parameters["weekday_availability"]
        microcycle_weekdays = parameters["microcycle_weekdays"]
        
        _, workout_time = user_workout_time(weekday_availability, microcycle_weekdays)
        
        return [
            workout_time
        ]

    def get_model_formatting_parameters(self, parameters):
        weekday_availability = parameters["weekday_availability"]
        microcycle_weekdays = parameters["microcycle_weekdays"]
        
        used_days, workout_time = user_workout_time(weekday_availability, microcycle_weekdays)
        
        return [
            parameters["phase_components"],
            used_days,
            workout_time,
            weekday_availability,
            microcycle_weekdays
        ]

    def format_class_specific_relaxation_history(self, formatted, attempt, workout_time):
        if workout_time is not None:
            formatted += f"Total Hours Allowed: {self._format_duration(workout_time)}\n"
        if attempt.microcycle_duration is not None:
            formatted += f"Total Time Used: {self._format_duration(attempt.microcycle_duration)}\n"
        return formatted

    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("Component", 12),
            "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
            "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
            "exercises_per_bodypart": ("Exercises Per Bodypart", 30),
            "partial_duration": ("Partial Duration", 35),
            "partial_duration_sec": ("Partial Duration in Seconds", 30),
            "duration": ("Duration", 35),
            "duration_sec": ("Duration in Seconds", 30),
        }

    def formatted_day(self, header_line, current_weekday_info, workday_index, used_days):
        line = ""
        line += f"\n| Day {workday_index + 1} {current_weekday_info["name"]:<{10}} Availability of {self._format_duration(used_days[workday_index]["availability"])} | \n"
        used_days[workday_index]["used"] = True
        line += header_line
        
        return line

    def line_fields(self, component_count, pc, metrics):
        (active_phase_components, exercises_per_bodypart_var, partial_duration_var, duration_var) = metrics

        # Format line
        return {
            "number": str(component_count + 1),
            "phase_component": f"{pc['name']}",
            "bodypart": pc["bodypart"],
            "exercises_per_bodypart": f"{self._format_range(str(exercises_per_bodypart_var), pc["exercises_per_bodypart_workout_min"], pc["exercises_per_bodypart_workout_max"])}",
            "partial_duration": f"{self._format_duration(partial_duration_var)} sec",
            "partial_duration_sec": f"{self._format_range(str(partial_duration_var) + " seconds", pc["duration_min"], pc["duration_max"])}",
            "duration": f"{self._format_duration(duration_var)} sec",
            "duration_sec": f"{self._format_range(str(duration_var) + " seconds", pc["duration_min"], pc["duration_max"] * pc["exercises_per_bodypart_workout_max"])}"
        }

    def formatted_counts(self, pcs, pc_count, longest_sizes):
        schedule_counts = f"\nPhase Component Counts:\n"
        schedule_not_included = f"\nNot Included Phase Components:\n"
        for pc_index, pc_no in enumerate(pc_count):
            pc = pcs[pc_index]
            phase_component_name = f"{pc['name']:<{longest_sizes['phase_component']+2}} {pc['bodypart']:<{longest_sizes['bodypart']+2}}"
            phase_component_frequency = self._format_range(pc_no, pc["frequency_per_microcycle_min"], pc["frequency_per_microcycle_max"])
            phase_component_required = f"Required Every Workout: {pc["required_every_workout"]}\t\tRequired Every Microcycle: {pc['required_within_microcycle']}"
            count_string = f"\t{phase_component_name}: {phase_component_frequency:<16} {phase_component_required}\n"
            if pc_no:
                schedule_counts += count_string
            elif pc_no == 0:
                schedule_not_included += count_string
        return schedule_counts + schedule_not_included + "\n"

    def format_agent_output(self, solution, formatted, schedule, phase_components, used_days, workout_time, weekday_availability, microcycle_weekdays):
        final_output = []

        phase_component_count = [0] * len(phase_components)

        # Calculate longest string sizes
        longest_sizes = {
            "phase_component": longest_string_size_for_key(phase_components[1:], "name"),
            "bodypart": longest_string_size_for_key(phase_components[1:], "bodypart")
        }

        # Create headers
        headers = self._create_header_fields(longest_sizes)
        
        # Create header line
        if SchedulerLoggingConfig.schedule: 
            formatted += self.schedule_title_line
            header_line = self.formatted_header_line(headers)

        for component_count, (phase_component_index, workday_index, *metrics) in enumerate(schedule):
            pc = phase_components[phase_component_index]

            (active_phase_components, exercises_per_bodypart_var, partial_duration_var, duration_var) = metrics

            if active_phase_components:
                final_output.append({
                    "workday_index": workday_index, 
                    "phase_component_index": phase_component_index, 
                    "phase_component_id": pc["id"],
                    "bodypart_id": pc["bodypart_id"],
                    "active_phase_components": active_phase_components, 
                    "duration_var": duration_var
                })

                current_weekday = microcycle_weekdays[workday_index]

                # Count the number of occurrences of each phase component
                phase_component_count[phase_component_index] += 1

                if SchedulerLoggingConfig.schedule:
                    if not used_days[workday_index]["used"]:
                        formatted += self.formatted_day(header_line, weekday_availability[current_weekday], workday_index, used_days)
                    line_fields = self.line_fields(component_count, pc, metrics)
                    formatted += self.formatted_schedule_line(headers, line_fields)
            else:
                if SchedulerLoggingConfig.schedule:
                    formatted += (f"Day {workday_index + 1}; Comp {component_count + 1}: \t----\n")
        
        if SchedulerLoggingConfig.counts:
            formatted += self.formatted_counts(phase_components, phase_component_count, longest_sizes)
        if SchedulerLoggingConfig.details:
            formatted += f"Total Time Used: {self._format_duration(solution['microcycle_duration'])}\n"
            formatted += f"Total Time Allowed: {self._format_duration(workout_time)}\n"

        return final_output, formatted

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
