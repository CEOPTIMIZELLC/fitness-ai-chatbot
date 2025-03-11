from ortools.sat.python import cp_model
from typing_extensions import TypedDict
import operator
from langchain_openai import ChatOpenAI
from datetime import datetime
from typing import Set, List, Optional
from dotenv import load_dotenv
from datetime import timedelta

from app.agents.agent_helpers import retrieve_relaxation_history, analyze_infeasibility
from app.agents.constraints import constrain_active_entries_vars, entry_within_min_max, no_consecutive_identical_active_items, no_n_active_items_without_desired_item, only_use_required_items, use_all_required_items


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

def build_opt_model_node(state: State, config=None) -> dict:
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

    # Integer variable representing the phase chosen at mesocycle i.
    mesocycle_vars = [
        model.NewIntVar(0, phase_amount - 1, f'mesocycle_{i}') 
        for i in range(max_mesocycles)]
    
    # Integer variable representing the duration of the phase in mesocycle i.
    duration_vars = [
        model.NewIntVar(0, macrocycle_allowed_weeks, f'duration_{i}') 
        for i in range(max_mesocycles)]

    # Boolean variables indicating whether phase j is used at mesocycle i.
    used_vars = [
        [
            model.NewBoolVar(f'mesocycle_{i}_is_phase_{j}') 
            for j in range(phase_amount)
        ] 
        for i in range(max_mesocycles)]

    # Boolean variables indicating whether mesocycle i is active.
    active_mesocycle_vars = [
        model.NewBoolVar(f'mesocycle_{i}_is_active') 
        for i in range(max_mesocycles)]

    # Introduce dynamic selection variables
    num_mesocycles_used = model.NewIntVar(min_mesocycles, max_mesocycles, 'num_mesocycles_used')

    model = constrain_active_entries_vars(model = model, 
                                          entry_vars = mesocycle_vars, 
                                          number_of_entries = max_mesocycles, 
                                          duration_vars = duration_vars, 
                                          active_entry_vars = active_mesocycle_vars)
    

    # Apply active constraints ======================================
    state["logs"] += "\nBuilding model with constraints:\n"

    # Constraint: The duration of a phase may only be a number of weeks between the minimum and maximum weeks allowed.
    if constraints["phase_within_min_max"]:
        model = entry_within_min_max(model = model, 
                                     items = phases, 
                                     entry_vars = mesocycle_vars, 
                                     number_of_entries = max_mesocycles, 
                                     used_vars = used_vars, 
                                     duration_vars = duration_vars)
        state["logs"] += "- Phase duration within min and max allowed weeks applied.\n"

    # Ensure total time does not exceed the macrocycle_allowed_weeks
    model.Add(num_mesocycles_used == sum(active_mesocycle_vars))
    model.Add(sum(duration_vars) <= macrocycle_allowed_weeks)

    # Constraint: No consecutive phases
    if constraints["no_consecutive_same_phase"]:
        model = no_consecutive_identical_active_items(model = model, 
                                                      entry_vars = mesocycle_vars, 
                                                      number_of_entries = max_mesocycles, 
                                                      active_entry_vars = active_mesocycle_vars)
        state["logs"] += "- No consecutive phase of the same type applied.\n"
    
    # Constraint: No 6 phases without stabilization endurance
    if constraints["no_6_phases_without_stab_end"]:
        stab_end_index = 1
        model = no_n_active_items_without_desired_item(model = model, 
                                                       allowed_n = 6, 
                                                       desired_item_index = stab_end_index, 
                                                       entry_vars = mesocycle_vars, 
                                                       number_of_entries = max_mesocycles, 
                                                       active_entry_vars = active_mesocycle_vars)
        state["logs"] += "- No 6 phases without stabilization endurance applied.\n"

    # Constraint: First phase is stabilization endurance
    if constraints["phase_1_is_stab_end"]:
        model.Add(mesocycle_vars[0] == 1)
        state["logs"] += "- First phase is stabilization endurance applied.\n"

    # Constraint: First phase is strength endurance
    if constraints["phase_2_is_str_end"]:
        model.Add(mesocycle_vars[1] == 2)
        state["logs"] += "- Second phase is strength endurance applied.\n"

    # Constraint: Only use required phases
    if constraints["only_use_required_phases"]:
        # Retrieves the index of all required phases.
        required_phases = [i for i, phase in enumerate(phases) if phase["required_phase"]]
        required_phases.append(0) # Include the inactive state.
        
        model = only_use_required_items(model = model, 
                                        required_items = required_phases, 
                                        entry_vars = mesocycle_vars)
        state["logs"] += "- Only use required phases applied.\n"

    # Constraint: Use all required phases at least once
    if constraints["use_all_required_phases"]:
        required_phases = [i for i, phase in enumerate(phases) if phase["required_phase"]]
        
        model = use_all_required_items(model = model, 
                                       required_items = required_phases, 
                                       entry_vars = mesocycle_vars, 
                                       number_of_entries = max_mesocycles)
        state["logs"] += "- Use every required phase at least once applied.\n"

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
                    model.AddMultiplicationEquality(goal_contrib, [duration_vars[i], used_vars[i][j], active_mesocycle_vars[i]])
                    goal_time_terms.append(goal_contrib)

        model.Add(goal_time == sum(goal_time_terms))


        # Secondary Objective: Maximize time spent in phases
        if constraints["maximize_phases"]:
            # Define total time used in all phases
            total_time = model.NewIntVar(0, macrocycle_allowed_weeks, 'total_time')
            model.Add(total_time == sum(duration_vars))

            # Define weighted objective
            model.Maximize(1000 * goal_time + total_time)  # Prioritize goal_time first, then total_time
            
        else:
            # Maximize goal time
            model.Maximize(goal_time)

        state["logs"] += "- Maximizing time spent on the goal phases.\n"


    return {"opt_model": (model, mesocycle_vars, duration_vars, used_vars, active_mesocycle_vars)}

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
- maximize_phases: Secondary objective to maximize the amount of time spent in phases in general.
- maximize_goal_phase: Objective to maximize the amount of time spent in the goal phase.
"""

    state = analyze_infeasibility(state, history, available_constraints)
    
    return {
        "constraints": state["constraints"],
        "current_attempt": state["current_attempt"]
    }

def solve_model_node(state: State, config=None) -> dict:
    """Solve model and record relaxation attempt results."""
    model, mesocycle_vars, duration_vars, used_vars, active_mesocycle_vars = state["opt_model"]

    phases = state["parameters"]["possible_phases"]

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

def format_solution_node(state: State, config=None) -> dict:
    """Format the optimization results."""
    solution = state["solution"]
    macrocycle_allowed_weeks = state["parameters"]["macrocycle_allowed_weeks"]
    phases = state["parameters"]["possible_phases"]
    longest_string_size = len(max(phases, key=lambda d:len(d["name"]))["name"])

    
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
            formatted += f"Total Weeks Allowed: {macrocycle_allowed_weeks}\n"
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
            phase_name = phases[phase_type]["name"]
            final_output.append({
                "name": phase_name,
                "id": phases[phase_type]["id"],
                "duration": phase_duration
            })
            formatted_duration = f"Duration: {phase_duration} weeks"
            formatted_goal_duration = f"Goal Duration: +{phase_duration if phases[phase_type]["is_goal_phase"] else 0} weeks"
            formatted_phase_minimum = f"min: {phases[phase_type]["element_minimum"]}"
            formatted_phase_maximum = f"max: {phases[phase_type]["element_maximum"]}"
            formatted += (f"Mesocycle {meso + 1}: \t{phase_name:<{longest_string_size+3}} ({formatted_duration}; {formatted_goal_duration}) [{formatted_phase_minimum} - {formatted_phase_maximum}]\n")
        formatted += f"\nTotal Goal Time: {solution['total_weeks_goal']} weeks\n"
        formatted += f"Total Time Used: {solution['total_weeks_time']} weeks\n"
        formatted += f"Total Time Allowed: {macrocycle_allowed_weeks} weeks\n"
        '''
        # Show final constraint status
        formatted += "\nFinal Constraint Status:\n"
        for constraint, active in state["constraints"].items():
            formatted += f"- {constraint}: {'Active' if active else 'Relaxed'}\n"
        '''

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
