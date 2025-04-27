from ortools.sat.python import cp_model
from typing_extensions import TypedDict
import operator
from langchain_openai import ChatOpenAI
from datetime import datetime
from typing import Set, List, Optional
from dotenv import load_dotenv
_ = load_dotenv()

class RelaxationAttempt:
    def __init__(self, constraints_relaxed: Set[str], result_feasible: bool, 
                 total_intensity: Optional[int] = None, reasoning: Optional[str] = None,
                 expected_impact: Optional[str] = None):
        self.constraints_relaxed = set(constraints_relaxed)
        self.result_feasible = result_feasible
        self.total_intensity = total_intensity
        self.timestamp = datetime.now()
        self.reasoning = reasoning
        self.expected_impact = expected_impact

class State(TypedDict):
    parameters: dict
    constraints: dict
    opt_model: any
    solution: any
    output: str
    logs: str
    relaxation_attempts: list
    current_attempt: dict  # Include reasoning and impact

def setup_params_node(state: State, config=None) -> dict:
    """Initialize optimization parameters and constraints."""
    parameters = {
        "microcycle_days": 10,
        "workout_days": [1,4,7],
        "workout_types": [0, 1, 2],  # 0: Recovery, 1: Moderate, 2: Heavy
        "heavy_value": 2,
    }
    
    # Define all constraints with their active status
    constraints = {
        "same_workout_days_1_2": True,     # Days 1 and 2 must be same type
        "no_consecutive_heavy": True,       # No consecutive heavy days
      #set to true to test infeasible constraint
        "workout_1_is_heavy": False,        # The workout on day 1 is a heavy day
        "maximize_intensity": True          # Objective function constraint
    }
    
    return {
        "parameters": parameters,
        "constraints": constraints,
        "opt_model": None,
        "solution": None,
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
    params = state["parameters"]
    constraints = state["constraints"]
    model = cp_model.CpModel()
    
    # Decision Variables
    num_days = params["microcycle_days"]
    workout_vars = [
        model.NewIntVar(min(params["workout_types"]),
                       max(params["workout_types"]),
                       f'workout_day_{d}')
        for d in range(num_days)
    ]
    heavy = params["heavy_value"]

    # Log which constraints are being applied
    state["logs"] += "\nBuilding model with constraints:\n"
    
    # Apply active constraints
    if constraints["same_workout_days_1_2"]:
        model.Add(workout_vars[0] == workout_vars[1])
        state["logs"] += "- Days 1 and 2 must be same type\n"

    if constraints["workout_1_is_heavy"]:
        model.Add(workout_vars[0] == 2)
        state["logs"] += "- Day 1 must be heavy\n"

    if constraints["no_consecutive_heavy"]:
        for d in range(num_days - 1):
            is_heavy_today = model.NewBoolVar(f'is_heavy_{d}')
            is_heavy_next = model.NewBoolVar(f'is_heavy_{d+1}')
            model.Add(workout_vars[d] == heavy).OnlyEnforceIf(is_heavy_today)
            model.Add(workout_vars[d] != heavy).OnlyEnforceIf(is_heavy_today.Not())
            model.Add(workout_vars[d+1] == heavy).OnlyEnforceIf(is_heavy_next)
            model.Add(workout_vars[d+1] != heavy).OnlyEnforceIf(is_heavy_next.Not())
            model.AddBoolOr([is_heavy_today.Not(), is_heavy_next.Not()])
        state["logs"] += "- No consecutive heavy days\n"

    if constraints["maximize_intensity"]:
        total_intensity = sum(workout_vars)
        model.Maximize(total_intensity)
        state["logs"] += "- Maximizing total intensity\n"

    return {"opt_model": (model, workout_vars)}

def analyze_infeasibility_node(state: State, config=None) -> dict:
    """Use LLM to analyze solver logs and suggest constraints to relax."""
    model = ChatOpenAI(temperature=0)
    
    # Prepare history of what's been tried
    history = []
    for attempt in state["relaxation_attempts"]:
        result = "successful" if attempt.result_feasible else "unsuccessful"
        history.append(
            f"Relaxed {attempt.constraints_relaxed}: {result}\n"
            f"Reasoning: {attempt.reasoning}\n"
            f"Impact: {attempt.expected_impact}\n"
        )
    
    prompt = f"""Given the optimization problem state, suggest which constraints to relax.

Current active constraints: {state['constraints']}

Previously attempted relaxations:
{chr(10).join(history) if history else "No previous attempts"}

Solver logs: {state['logs']}

Important considerations:
1. We want to relax as few constraints as possible!!! Aim for 1 only!
2. Avoid suggesting combinations that have already failed
3. Consider relaxing multiple constraints only if single relaxations haven't worked
4. Consider that we want to maximize the objective function as much as possible when you choose what to relax

Available constraints:
- workout_1_is_heavy: Forces Day 1 to be heavy
- same_workout_days_1_2: Forces days 1 and 2 to have same workout type
- no_consecutive_heavy: Prevents consecutive heavy workout days
- maximize_intensity: Objective to maximize overall workout intensity

Return your response as a dictionary:
{{
    'constraints_to_relax': ['constraint_name1'],  # List of constraints to try relaxing
    'reasoning': 'explanation',   # Why relaxing this constraint would lead to better optimization of the objective function than the others
    'expected_impact': 'impact'   # Expected effect on training quality
}}
"""

    response = model.invoke(prompt)
    suggestion = eval(response.content)
    
    # Store LLM's analysis
    state["logs"] += "\nLLM Analysis:\n"
    state["logs"] += f"Suggested relaxations: {suggestion['constraints_to_relax']}\n"
    state["logs"] += f"Reasoning: {suggestion['reasoning']}\n"
    state["logs"] += f"Expected Impact: {suggestion['expected_impact']}\n"
    
    # Reset all constraints to active
    for constraint in state["constraints"]:
        state["constraints"][constraint] = True
    
    # Apply suggested relaxations
    for constraint in suggestion['constraints_to_relax']:
        state["constraints"][constraint] = False
    
    # Update current attempt info
    state["current_attempt"] = {
        "constraints": set(suggestion['constraints_to_relax']),
        "reasoning": suggestion['reasoning'],
        "expected_impact": suggestion['expected_impact']
    }
    
    return {
        "constraints": state["constraints"],
        "current_attempt": state["current_attempt"]
    }

def solve_model_node(state: State, config=None) -> dict:
    """Solve model and record relaxation attempt results."""
    model, workout_vars = state["opt_model"]
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    status = solver.Solve(model)
    
    state["logs"] += f"\nSolver status: {status}\n"
    state["logs"] += f"Conflicts: {solver.NumConflicts()}, Branches: {solver.NumBranches()}\n"
    
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        schedule = [solver.Value(var) for var in workout_vars]
        total_intensity = sum(schedule)
        solution = {
            "schedule": schedule,
            "total_intensity": total_intensity,
            "status": status
        }
        
        # Record successful attempt
        attempt = RelaxationAttempt(
            state["current_attempt"]["constraints"],
            True,
            total_intensity,
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

def format_solution_node(state: State, config=None) -> dict:
    """Format the optimization results."""
    solution = state["solution"]
    
    formatted = "Optimization Results:\n"
    formatted += "=" * 50 + "\n\n"
    
    # Show relaxation attempts history
    formatted += "Relaxation Attempts:\n"
    formatted += "-" * 40 + "\n"
    for i, attempt in enumerate(state["relaxation_attempts"], 1):
        formatted += f"\nAttempt {i}:\n"
        formatted += f"Constraints relaxed: {attempt.constraints_relaxed}\n"
        formatted += f"Result: {'Feasible' if attempt.result_feasible else 'Infeasible'}\n"
        if attempt.total_intensity is not None:
            formatted += f"Total Intensity: {attempt.total_intensity}\n"
        if attempt.reasoning:
            formatted += f"Reasoning: {attempt.reasoning}\n"
        if attempt.expected_impact:
            formatted += f"Expected Impact: {attempt.expected_impact}\n"
        formatted += f"Timestamp: {attempt.timestamp}\n"
    
    if solution is None:
        formatted += "\nNo valid schedule found even with relaxed constraints.\n"
    else:
        schedule = solution["schedule"]
        workout_labels = {0: "Recovery", 1: "Moderate", 2: "Heavy"}
        
        formatted += "\nFinal Training Schedule:\n"
        formatted += "-" * 40 + "\n"
        
        for day, intensity in enumerate(schedule):
            label = workout_labels.get(intensity, str(intensity))
            formatted += f"Day {day + 1}: {label} (Intensity: {intensity})\n"
        
        formatted += f"\nTotal Intensity: {solution['total_intensity']}\n"
        
        # Show final constraint status
        formatted += "\nFinal Constraint Status:\n"
        for constraint, active in state["constraints"].items():
            formatted += f"- {constraint}: {'Active' if active else 'Relaxed'}\n"
    
    return {"output": formatted}

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

if __name__ == "__main__":
    # Create and run the graph
    graph = create_optimization_graph()
    
    initial_state = {
        "parameters": {},
        "constraints": {},
        "opt_model": None,
        "solution": None,
        "output": "",
        "logs": "",
        "relaxation_attempts": [],
        "current_attempt": {"constraints": set(), "reasoning": None, "expected_impact": None}
    }
    
    result = graph.invoke(initial_state)
    print(result["output"])