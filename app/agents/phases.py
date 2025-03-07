from ortools.sat.python import cp_model
from typing_extensions import TypedDict
import operator
from langchain_openai import ChatOpenAI
from datetime import datetime
from typing import Set, List, Optional
from dotenv import load_dotenv
from datetime import timedelta

from app.agents.agent_helpers import retrieve_relaxation_history, analyze_infeasibility

_ = load_dotenv()

class RelaxationAttempt:
    def __init__(self, constraints_relaxed: Set[str], result_feasible: bool, 
                 total_weeks_goal: Optional[int] = None, total_weeks_time: Optional[int] = None, 
                 reasoning: Optional[str] = None, expected_impact: Optional[str] = None):
        self.constraints_relaxed = set(constraints_relaxed)
        self.result_feasible = result_feasible
        self.total_weeks_goal = total_weeks_goal
        self.total_weeks_time = total_weeks_time
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
        "macrocycle_allowed_weeks": 43,
        "possible_phases": {
            "stabilization endurance": {
                "id": 1,
                "phase_duration_minimum_in_weeks": 4,
                "phase_duration_maximum_in_weeks": 6,
                "required_phase": True,
                "is_goal_phase": True
            },
            "strength endurance": {
                "id": 2,
                "phase_duration_minimum_in_weeks": 3,
                "phase_duration_maximum_in_weeks": 7,
                "required_phase": True,
                "is_goal_phase": False
            },
            "hypertrophy": {
                "id": 3,
                "phase_duration_minimum_in_weeks": 3,
                "phase_duration_maximum_in_weeks": 5,
                "required_phase": True,
                "is_goal_phase": False
            },
            "maximal strength": {
                "id": 4,
                "phase_duration_minimum_in_weeks": 4,
                "phase_duration_maximum_in_weeks": 4,
                "required_phase": True,
                "is_goal_phase": True
            },
            "power": {
                "id": 5,
                "phase_duration_minimum_in_weeks": 2,
                "phase_duration_maximum_in_weeks": 6,
                "required_phase": True,
                "is_goal_phase": False
            }
        }
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

def build_opt_model_node(state: State, config=None) -> dict:
    """Build the optimization model with active constraints."""
    parameters = state["parameters"]
    constraints = state["constraints"]
    model = cp_model.CpModel()

    macrocycle_allowed_weeks = parameters["macrocycle_allowed_weeks"]
    phases = parameters["possible_phases"]
    phase_names = list(phases.keys())

    # Define variables =====================================

    # Upper bound on number of mesocycles (greedy estimation)
    num_mesocycles = macrocycle_allowed_weeks // min(phase["phase_duration_minimum_in_weeks"] for phase in phases.values())

    # Integer variable representing the phase chosen at mesocycle i.
    mesocycle_vars = [
        model.NewIntVar(0, len(phase_names) - 1, f'mesocycle_{i}') 
        for i in range(num_mesocycles)]
    
    # Integer variable representing the duration of the phase in mesocycle i.
    duration_vars = [
        model.NewIntVar(0, macrocycle_allowed_weeks, f'duration_{i}') 
        for i in range(num_mesocycles)]

    # Boolean variables indicating whether phase j is used at mesocycle i.
    used_vars = [
        [
            model.NewBoolVar(f'mesocycle_{i}_is_phase_{j}') 
            for j in range(len(phase_names))
        ] 
        for i in range(num_mesocycles)]

    # Apply active constraints ======================================
    state["logs"] += "\nBuilding model with constraints:\n"

    # Constraint: The duration of a phase may only be a number of weeks between the minimum and maximum weeks allowed.
    if constraints["phase_within_min_max"]:
        for i in range(num_mesocycles):
            for j, phase in enumerate(phases):
                # Ensures that if a state is chosen (used_vars[i][j] is True), then:
                # The corresponding state_vars[i] must match the index j.
                model.Add(mesocycle_vars[i] == j).OnlyEnforceIf(used_vars[i][j])

                # The duration_vars[i] must be within the allowed range.
                model.Add(duration_vars[i] >= phases[phase]["phase_duration_minimum_in_weeks"]).OnlyEnforceIf(used_vars[i][j])
                model.Add(duration_vars[i] <= phases[phase]["phase_duration_maximum_in_weeks"]).OnlyEnforceIf(used_vars[i][j])        
        state["logs"] += "- Phase duration within min and max allowed weeks applied.\n"

    # Ensure total time does not exceed the macrocycle_allowed_weeks
    model.Add(sum(duration_vars) <= macrocycle_allowed_weeks)

    # Constraint: No consecutive phases
    if constraints["no_consecutive_same_phase"]:
        # For each mesocycle in the macrocycle make sure that the mesocycle at the current index isn't the same as the mesocyle at the next index.
        for i in range(num_mesocycles - 1):
            model.Add(mesocycle_vars[i] != mesocycle_vars[i + 1])
        state["logs"] += "- No consecutive phase of the same type applied.\n"
    
    # Constraint: No 6 phases without stabilization endurance
    if constraints["no_6_phases_without_stab_end"]:
        stab_end_index = phase_names.index("stabilization endurance")
        
        # The following is a sliding window of 6 phases that ensures that at least one will be stabilization endurance.
        for i in range(num_mesocycles - 5):  # Ensure we have a window of 6
            # Boolean variables for the window, indicating whether phase j in the 6 phase window is stabilization endurance.
            stab_end_in_window = [
                model.NewBoolVar(f'stab_end_{j}') 
                for j in range(i, i + 6)]
            
            # For each phase in the window
            for j, var in zip(range(i, i + 6), stab_end_in_window):
                # Ensures that, if the phase in the window is stabilization endurance:
                # then the mesocycle at the corresponding index will be set to stabilization endurance.
                model.Add(mesocycle_vars[j] == stab_end_index).OnlyEnforceIf(var)
                model.Add(mesocycle_vars[j] != stab_end_index).OnlyEnforceIf(var.Not())
            
            # Ensures that at least one of the phases in the window will be stabilization endurance.
            model.AddBoolOr(stab_end_in_window)
        state["logs"] += "- No 6 phases without stabilization endurance applied.\n"

    # Constraint: First phase is stabilization endurance
    if constraints["phase_1_is_stab_end"]:
        model.Add(mesocycle_vars[0] == phase_names.index("stabilization endurance"))
        state["logs"] += "- First phase is stabilization endurance applied.\n"

    # Constraint: First phase is strength endurance
    if constraints["phase_2_is_str_end"]:
        model.Add(mesocycle_vars[1] == phase_names.index("strength endurance"))
        state["logs"] += "- Second phase is strength endurance applied.\n"

    # Constraint: Only use required phases
    if constraints["only_use_required_phases"]:
        # Retrieves the index of all required phases.
        required_phases = [i for i, phase in enumerate(phase_names) if phases[phase]["required_phase"]]
        
        # Ensures that only required phases will be used at any mesocycle in the macrocycle.
        for mesocycle in mesocycle_vars:
            model.AddAllowedAssignments([mesocycle], [(phase,) for phase in required_phases])
        state["logs"] += "- Only use required phases applied.\n"

    # Constraint: Only all required phases at least once
    if constraints["use_all_required_phases"]:
        required_phase_indices = [i for i, phase in enumerate(phase_names) if phases[phase]["required_phase"]]
        
        for phase_index in required_phase_indices:
            # Create an array of Boolean variables indicating whether this phase appears in each mesocycle
            phase_in_mesocycles = [
                model.NewBoolVar(f'phase_{phase_index}_in_mesocycle_{i}') 
                for i in range(num_mesocycles)]
            
            for i in range(num_mesocycles):
                model.Add(mesocycle_vars[i] == phase_index).OnlyEnforceIf(phase_in_mesocycles[i])
                model.Add(mesocycle_vars[i] != phase_index).OnlyEnforceIf(phase_in_mesocycles[i].Not())

            # Ensure that at least one of these Boolean variables is true
            model.AddBoolOr(phase_in_mesocycles)
        state["logs"] += "- Use every required phase at least once applied.\n"

    # Objective: Maximize time spent on goal phases
    if constraints["maximize_goal_phase"]:
        # List of contributions to goal time.
        goal_time_terms = []

        # Creates goal_time, which will hold the total time spent in goal states.
        goal_time = model.NewIntVar(0, macrocycle_allowed_weeks, 'goal_time')
        for i in range(num_mesocycles):
            for j, phase in enumerate(phases):
                if phases[phase]["is_goal_phase"]:
                    # Helper variable to store phase's contribution.
                    goal_contrib = model.NewIntVar(0, macrocycle_allowed_weeks, f'goal_contrib_{i}_{j}')

                    # If a goal state is used, its duration contributes to goal_time.
                    model.AddMultiplicationEquality(goal_contrib, [duration_vars[i], used_vars[i][j]])
                    goal_time_terms.append(goal_contrib)
        
        model.Add(goal_time == sum(goal_time_terms))
        
        # Maximize goal time
        model.Maximize(goal_time)

        state["logs"] += "- Maximizing time spent on the goal phases.\n"


    return {"opt_model": (model, mesocycle_vars, duration_vars, used_vars)}

def analyze_infeasibility_node(state: State, config=None) -> dict:
    """Use LLM to analyze solver logs and suggest constraints to relax."""
    # Prepare history of what's been tried
    history = retrieve_relaxation_history(state["relaxation_attempts"])

    available_constraints = """
- no_consecutive_same_phase: Prevents consecutive phases of the same type.
- phase_within_min_max: Forces the duration of a phase to be between the minimum and maximum values allowed.
- phase_1_is_stab_end: Forces the first phase of a macrocycle to be a stabilization endurance phase.
- phase_2_is_str_end: Forces the second phase of a macrocycle to be a strength endurance phase.
- no_6_phases_without_stab_end: Prevents 6 months from passing without a stabilization endurance phase.
- only_use_required_phases: Prevents mesocycle_vars from being given a phase that isn't required.
- use_all_required_phases: Forces all required phases to be assigned at lease once in a macrocycle.
- maximize_goal_phase: Objective to maximize the amount of time spend in the goal phase.
"""

    state = analyze_infeasibility(state, history, available_constraints)
    
    return {
        "constraints": state["constraints"],
        "current_attempt": state["current_attempt"]
    }

def solve_model_node(state: State, config=None) -> dict:
    """Solve model and record relaxation attempt results."""
    model, mesocycle_vars, duration_vars, used_vars = state["opt_model"]

    phases = state["parameters"]["possible_phases"]
    phase_names = list(phases.keys())

    solver = cp_model.CpSolver()
    #solver.parameters.log_search_progress = True
    status = solver.Solve(model)
    
    state["logs"] += f"\nSolver status: {status}\n"
    state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"
    
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        total_weeks_goal = 0
        total_weeks_time = 0
        schedule = []
        for i in range(len(mesocycle_vars)):
            phase_type = solver.Value(mesocycle_vars[i])
            phase_name = phase_names[phase_type]
            phase_duration = solver.Value(duration_vars[i])
            
            # Sum of all mesocycle_vars.
            total_weeks_time += phase_duration
            
            schedule.append((phase_type, phase_duration))
            if phases[phase_name]["is_goal_phase"]:
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

def format_solution_node(state: State, config=None) -> dict:
    """Format the optimization results."""
    solution = state["solution"]
    macrocycle_allowed_weeks = state["parameters"]["macrocycle_allowed_weeks"]
    phases = state["parameters"]["possible_phases"]
    phase_names = list(phases.keys())
    
    formatted = "Optimization Results:\n"
    formatted += "=" * 50 + "\n\n"
    
    # Show relaxation attempts history
    formatted += "Relaxation Attempts:\n"
    formatted += "-" * 40 + "\n"
    for i, attempt in enumerate(state["relaxation_attempts"], 1):
        formatted += f"\nAttempt {i}:\n"
        formatted += f"Constraints relaxed: {attempt.constraints_relaxed}\n"
        formatted += f"Result: {'Feasible' if attempt.result_feasible else 'Infeasible'}\n"
        if macrocycle_allowed_weeks is not None:
            formatted += f"Total Weeks Alloed: {macrocycle_allowed_weeks}\n"
        if attempt.total_weeks_goal is not None:
            formatted += f"Total Goal Time in Weeks: {attempt.total_weeks_goal}\n"
        if attempt.total_weeks_time is not None:
            formatted += f"Total Macrocycle Length in Weeks: {attempt.total_weeks_time}\n"
        if attempt.reasoning:
            formatted += f"Reasoning: {attempt.reasoning}\n"
        if attempt.expected_impact:
            formatted += f"Expected Impact: {attempt.expected_impact}\n"
        formatted += f"Timestamp: {attempt.timestamp}\n"
    
    final_output = []

    if solution is None:
        formatted += "\nNo valid schedule found even with relaxed constraints.\n"
    else:
        
        schedule = solution["schedule"]
        
        formatted += "\nFinal Training Schedule:\n"
        formatted += "-" * 40 + "\n"
        
        for meso, (phase_type, phase_duration) in enumerate(schedule):
            phase_name = phase_names[phase_type]
            final_output.append({
                "name": phase_name,
                "id": phases[phase_name]["id"],
                "duration": phase_duration
            })
            formatted += f"Mesocycle {meso + 1}: {phase_name} (Duration: {phase_duration} weeks, Time spent in goal phase: +{phase_duration if phases[phase_name]["is_goal_phase"] else 0} weeks)\n"
        
        formatted += f"\nTotal Goal Time: {solution['total_weeks_goal']} weeks\n"
        formatted += f"Total Time: {solution['total_weeks_time']} weeks\n"
        
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
    builder.add_node("analyze", analyze_infeasibility_node)
    builder.add_node("format", format_solution_node)

    # Add edges
    builder.add_edge(START, "setup")
    builder.add_edge("setup", "build")
    builder.add_edge("build", "solve")

    def solution_router(state: State, config=None):
        if state["solution"] is None and any(state["constraints"].values()):
            return "analyze"  # Try relaxing a constraint
        return "format"      # Either solution found or no more constraints to relax

    builder.add_conditional_edges(
        "solve",
        solution_router,
        {
            "analyze": "analyze",
            "format": "format"
        }
    )

    builder.add_edge("analyze", "build")
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
    Main()
