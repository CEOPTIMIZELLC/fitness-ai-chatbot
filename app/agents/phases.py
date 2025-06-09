from config import ortools_solver_time_in_seconds, log_schedule, log_details
from ortools.sat.python import cp_model
from typing import Set, Optional
from dotenv import load_dotenv

from app.agents.constraints import (
    link_entry_and_item, 
    constrain_active_entries_vars, 
    entries_within_min_max, 
    no_consecutive_identical_items, 
    no_n_items_without_desired_item, 
    only_use_required_items, 
    use_all_required_items)

from app.agents.base_agent import BaseRelaxationAttempt, BaseAgent, BaseAgentState
from app.utils.longest_string import longest_string_size_for_key

_ = load_dotenv()

available_constraints = """
- phase_2_is_str_end: Forces second phase to be strength endurance
- only_use_required_phases: Only use phases that are required
- use_all_required_phases: Use every required phase at least once
- phase_duration_within_min_max: Forces the duration of a phase to be between the minimum and maximum values allowed.
- no_consecutive_identical_phases: Prevents consecutive identical phases
- no_n_phases_without_goal: Prevents n phases without including the goal phase
- maximize_phases: Secondary objective to maximize the amount of time spent in phases in general.
- maximize_goal_phase: Objective to maximize the amount of time spent in the goal phase.
"""

class RelaxationAttempt(BaseRelaxationAttempt):
    def __init__(self, 
                 constraints_relaxed: Set[str], 
                 result_feasible: bool, 
                 total_weeks_goal: Optional[int] = None, 
                 total_weeks_time: Optional[int] = None, 
                 reasoning: Optional[str] = None, 
                 expected_impact: Optional[str] = None):
        super().__init__(constraints_relaxed, result_feasible, reasoning, expected_impact)
        self.total_weeks_goal = total_weeks_goal
        self.total_weeks_time = total_weeks_time

class State(BaseAgentState):
    parameter_input: dict

class PhaseAgent(BaseAgent):
    available_constraints = available_constraints

    def __init__(self, parameters={}, constraints={}):
        super().__init__()
        self.initial_state["parameter_input"]={
            "parameters": parameters, 
            "constraints": constraints}

    def setup_params_node(self, state: State, config=None) -> dict:

        parameter_input = state.get("parameter_input", {})

        """Initialize optimization parameters and constraints."""
        parameters = {
            "macrocycle_allowed_weeks": 43,
            "possible_phases": [
                {"id": 0,"name":"inactive","element_minimum": 0,"element_maximum": 0,"required_phase": False,"is_goal_phase": False},
                {"id": 1,"name":"stabilization endurance","element_minimum": 4,"element_maximum": 6,"required_phase": True,"is_goal_phase": False},
                {"id": 2,"name":"strength endurance","element_minimum": 3,"element_maximum": 7,"required_phase": True,"is_goal_phase": False},
                {"id": 3,"name":"hypertrophy","element_minimum": 3,"element_maximum": 5,"required_phase": True,"is_goal_phase": True},
                {"id": 4,"name":"maximal strength","element_minimum": 4,"element_maximum": 4,"required_phase": False,"is_goal_phase": False},
                {"id": 5,"name":"power","element_minimum": 2,"element_maximum": 6,"required_phase": True,"is_goal_phase": True}
            ]
        }

        # Define all constraints with their active status
        constraints = {
            "no_consecutive_same_phase": True,          # No consecutive phases of the same type.
            "phase_within_min_max": True,               # The duration of a phase may only be a number of weeks between the minimum and maximum weeks allowed.
            "phase_1_is_stab_end": True,                # The first phase for a macrocycle is stabilization endurance.
            "phase_2_is_str_end": True,                 # The second phase for a macrocycle is strength endurance.
            "no_6_phases_without_stab_end": True,       # If it has been 6 phases without going to stabilization endurance, go to stabilization endurance.
            "only_use_required_phases": True,           # A mesocycle may only be a phase that is labeled as "required".
            "use_all_required_phases": True,            # At least one mesocycle should be given each phase that is labeled as "required".
            "maximize_phases": True,                    # Objective function constraint
            "maximize_goal_phase": True                 # Objective function constraint
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
    
    def create_model_vars(self, model, macrocycle_allowed_weeks, phases, phase_amount, min_mesocycles, max_mesocycles):
        vars = {}

        # Integer variable representing the phase chosen at mesocycle i.
        vars["mesocycles"] = [
            model.NewIntVar(0, phase_amount - 1, f'mesocycle_{i}') 
            for i in range(max_mesocycles)]

        # Integer variable representing the duration of the phase in mesocycle i.
        vars["duration"] = [
            model.NewIntVar(0, macrocycle_allowed_weeks, f'duration_{i}') 
            for i in range(max_mesocycles)]

        # Boolean variables indicating whether phase j is used at mesocycle i.
        vars["used"] = [[
            model.NewBoolVar(f'mesocycle_{i}_is_phase_{j}') 
            for j in range(phase_amount)]
            for i in range(max_mesocycles)]

        # Boolean variables indicating whether mesocycle i is active.
        vars["active_mesocycles"] = [
            model.NewBoolVar(f'mesocycle_{i}_is_active') 
            for i in range(max_mesocycles)]

        # Introduce dynamic selection variables
        vars["num_mesocycles_used"] = model.NewIntVar(min_mesocycles, max_mesocycles, 'num_mesocycles_used')

        constrain_active_entries_vars(model = model, 
                                      entry_vars = vars["mesocycles"], 
                                      number_of_entries = max_mesocycles, 
                                      duration_vars = vars["duration"], 
                                      active_entry_vars = vars["active_mesocycles"])

        link_entry_and_item(model = model, 
                            items = phases, 
                            entry_vars = vars["mesocycles"], 
                            number_of_entries = max_mesocycles, 
                            used_vars = vars["used"])
        return vars

    def apply_model_constraints(self, constraints, model, vars, phases, macrocycle_allowed_weeks, max_mesocycles):
        # Apply active constraints ======================================
        logs = "\nBuilding model with constraints:\n"

        # Constraint: The duration of a phase may only be a number of weeks between the minimum and maximum weeks allowed.
        if constraints["phase_within_min_max"]:
            entries_within_min_max(model = model, 
                                   items = phases, 
                                   minimum_key="element_minimum", 
                                   maximum_key="element_maximum",
                                   number_of_entries = max_mesocycles, 
                                   used_vars = vars["used"], 
                                   duration_vars = vars["duration"])
            logs += "- Phase duration within min and max allowed weeks applied.\n"

        # Ensure total time does not exceed the macrocycle_allowed_weeks
        model.Add(vars["num_mesocycles_used"] == sum(vars["active_mesocycles"]))
        model.Add(sum(vars["duration"]) <= macrocycle_allowed_weeks)

        # Constraint: No consecutive phases
        if constraints["no_consecutive_same_phase"]:
            no_consecutive_identical_items(model = model, 
                                           entry_vars = vars["mesocycles"], 
                                           active_entry_vars = vars["active_mesocycles"])
            logs += "- No consecutive phase of the same type applied.\n"

        # Constraint: No 6 phases without stabilization endurance
        if constraints["no_6_phases_without_stab_end"]:
            stab_end_index = 1
            no_n_items_without_desired_item(model = model, 
                                            allowed_n = 6, 
                                            desired_item_index = stab_end_index, 
                                            entry_vars = vars["mesocycles"], 
                                            number_of_entries = max_mesocycles, 
                                            active_entry_vars = vars["active_mesocycles"])
            logs += "- No 6 phases without stabilization endurance applied.\n"

        # Constraint: First phase is stabilization endurance
        if constraints["phase_1_is_stab_end"]:
            model.Add(vars["mesocycles"][0] == 1)
            logs += "- First phase is stabilization endurance applied.\n"

        # Constraint: First phase is strength endurance
        if constraints["phase_2_is_str_end"]:
            model.Add(vars["mesocycles"][1] == 2)
            logs += "- Second phase is strength endurance applied.\n"

        # Constraint: Only use required phases
        if constraints["only_use_required_phases"]:
            # Retrieves the index of all required phases.
            required_phases = [i for i, phase in enumerate(phases) if phase["required_phase"]]
            required_phases.append(0) # Include the inactive state.

            only_use_required_items(model = model, 
                                    required_items = required_phases, 
                                    entry_vars = vars["mesocycles"])
            logs += "- Only use required phases applied.\n"

        # Constraint: Use all required phases at least once
        if constraints["use_all_required_phases"]:
            required_phases = [i for i, phase in enumerate(phases) if phase["required_phase"]]

            use_all_required_items(model = model, 
                                   required_items = required_phases, 
                                   used_vars = vars["used"])
            logs += "- Use every required phase at least once applied.\n"
        return logs

    def apply_model_objective(self, constraints, model, vars, phases, macrocycle_allowed_weeks, max_mesocycles):
        logs = ""

        # Objective: Maximize time spent on goal phases
        if constraints["maximize_goal_phase"]:
            # List of contributions to goal time.
            goal_time_terms = []

            # Creates goal_time, which will hold the total time spent in goal states.
            goal_time = model.NewIntVar(0, macrocycle_allowed_weeks, 'goal_time')
            for i in range(max_mesocycles):
                for j, phase in enumerate(phases):
                    if phase["is_goal_phase"]:
                        # Helper variable to store phase's contribution.
                        goal_contrib = model.NewIntVar(0, macrocycle_allowed_weeks, f'goal_contrib_{i}_{j}')

                        # If a goal state is used, its duration contributes to goal_time.
                        model.AddMultiplicationEquality(goal_contrib, [vars["duration"][i], vars["used"][i][j], vars["active_mesocycles"][i]])
                        goal_time_terms.append(goal_contrib)

            model.Add(goal_time == sum(goal_time_terms))

            # Secondary Objective: Maximize time spent in phases
            if constraints["maximize_phases"]:
                # Define total time used in all phases
                total_time = model.NewIntVar(0, macrocycle_allowed_weeks, 'total_time')
                model.Add(total_time == sum(vars["duration"]))

                # Define weighted objective
                model.Maximize(1000 * goal_time + total_time)  # Prioritize goal_time first, then total_time

            else:
                # Maximize goal time
                model.Maximize(goal_time)

            logs += "- Maximizing time spent on the goal phases.\n"
        return logs

    def build_opt_model_node(self, state: State, config=None) -> dict:
        """Build the optimization model with active constraints."""
        parameters = state["parameters"]
        constraints = state["constraints"]
        model = cp_model.CpModel()

        macrocycle_allowed_weeks = parameters["macrocycle_allowed_weeks"]
        phases = parameters["possible_phases"]
        phase_amount = len(phases)

        # Define variables =====================================

        # Upper bound on number of mesocycles (greedy estimation)
        min_mesocycles = macrocycle_allowed_weeks // max(phase["element_maximum"] for phase in phases[1:])
        max_mesocycles = macrocycle_allowed_weeks // min(phase["element_minimum"] for phase in phases[1:])

        vars = self.create_model_vars(model, macrocycle_allowed_weeks, phases, phase_amount, min_mesocycles, max_mesocycles)
        state["logs"] += self.apply_model_constraints(constraints, model, vars, phases, macrocycle_allowed_weeks, max_mesocycles)
        state["logs"] += self.apply_model_objective(constraints, model, vars, phases, macrocycle_allowed_weeks, max_mesocycles)

        return {"opt_model": (model, vars["mesocycles"], vars["duration"], vars["used"], vars["active_mesocycles"])}

    def solve_model_node(self, state: State, config=None) -> dict:
        """Solve model and record relaxation attempt results."""
        model, mesocycle_vars, duration_vars, used_vars, active_mesocycle_vars = state["opt_model"]

        phases = state["parameters"]["possible_phases"]

        solver = cp_model.CpSolver()
        # solver.parameters.log_search_progress = True
        solver.parameters.max_time_in_seconds = ortools_solver_time_in_seconds

        status = self._solve_and_time_solver(solver, model)

        state["logs"] += f"\nSolver status: {status}\n"
        state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"

        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            total_weeks_goal = total_weeks_time = 0
            schedule = []
            for i in range(len(mesocycle_vars)):
                # Ensure that the mesocycle is active
                if solver.Value(active_mesocycle_vars[i]):
                    phase_type = solver.Value(mesocycle_vars[i])
                    phase_duration = solver.Value(duration_vars[i])

                    # Sum of all mesocycle_vars.
                    total_weeks_time += phase_duration

                    schedule.append((phase_type, phase_duration))
                    if phases[phase_type]["is_goal_phase"]:
                        total_weeks_goal += phase_duration
            solution = {
                "schedule": schedule,
                "total_weeks_goal": total_weeks_goal,
                "total_weeks_time": total_weeks_time,
                "status": status
            }

            # Record successful attempt
            attempt = RelaxationAttempt(
                state["current_attempt"]["constraints"],
                True,
                total_weeks_goal,
                total_weeks_time,
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
            state["current_attempt"]["reasoning"],
            state["current_attempt"]["expected_impact"]
        )
        state["relaxation_attempts"].append(attempt)
        return {"solution": None}

    def get_relaxation_formatting_parameters(self, parameters):
        return [
            parameters["macrocycle_allowed_weeks"],
        ]

    def get_model_formatting_parameters(self, parameters):
        return [
            parameters["possible_phases"], 
            parameters["macrocycle_allowed_weeks"],
        ]

    def format_class_specific_relaxation_history(self, formatted, attempt, macrocycle_allowed_weeks):
        if macrocycle_allowed_weeks is not None:
            formatted += f"Total Weeks Allowed: {macrocycle_allowed_weeks}\n"
        if attempt.total_weeks_goal is not None:
            formatted += f"Total Goal Time in Weeks: {attempt.total_weeks_goal}\n"
        if attempt.total_weeks_time is not None:
            formatted += f"Total Macrocycle Length in Weeks: {attempt.total_weeks_time}\n"
        return formatted

    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("Mesocycle", 12),
            "phase": ("Phase", longest_sizes["phase"] + 4),
            "duration": ("Duration", 17),
            "goal_duration": ("Goal Duration", 17),
        }

    def formatted_schedule(self, headers, i, phase, phase_duration):
        # Format line
        line_fields = {
            "number": str(i + 1),
            "phase": f"{phase['name']}",
            "duration": f"{self._format_range(str(phase_duration), phase["element_minimum"], phase["element_maximum"])} weeks",
            "goal_duration": f"+{phase_duration if phase['is_goal_phase'] else 0} weeks"
        }

        line = ""
        for field, (_, length) in headers.items():
            line += self._create_formatted_field(field, line_fields[field], length)
        return line + "\n"

    def format_agent_output(self, solution, formatted, schedule, phases, macrocycle_allowed_weeks):
        final_output = []

        # Calculate longest string sizes
        longest_sizes = {"phase": longest_string_size_for_key(phases, "name")}

        # Create headers
        headers = self._create_header_fields(longest_sizes)

        # Create header line
        if log_schedule: 
            formatted += self.formatted_header_line(headers)

        for i, (phase_type, phase_duration) in enumerate(schedule):
            phase = phases[phase_type]
            final_output.append({
                "name": phase["name"],
                "id": phase["id"],
                "is_goal_phase": phase["is_goal_phase"],
                "duration": phase_duration
            })

            if log_schedule:
                formatted += self.formatted_schedule(headers, i, phase, phase_duration)

        if log_details:
            formatted += f"\nTotal Goal Time: {solution['total_weeks_goal']} weeks\n"
            formatted += f"Total Time Used: {solution['total_weeks_time']} weeks\n"
            formatted += f"Total Time Allowed: {macrocycle_allowed_weeks} weeks\n"

        return final_output, formatted

    def run(self):
        graph = self.create_optimization_graph(State)
        result = graph.invoke(self.initial_state)
        return result

def Main(parameters=None, constraints=None):
    agent = PhaseAgent(parameters, constraints)
    result = agent.run()
    return {"formatted": result["formatted"], "output": result["output"], "solution": result["solution"]}

if __name__ == "__main__":
    result = Main()
    print(result["formatted"])
