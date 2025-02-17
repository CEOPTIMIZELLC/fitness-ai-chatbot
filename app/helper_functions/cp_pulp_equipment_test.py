from typing_extensions import TypedDict
import operator
from langchain_openai import ChatOpenAI
from datetime import datetime
from typing import Set, List, Optional
from dotenv import load_dotenv
import pulp

from sqlalchemy import text
from app import db
from app.models import Users, Equipment_Library, Exercise_Equipment, Exercise_Library, User_Equipment

from flask_login import current_user

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
    sql_query: str
    query_result: str
    query_rows: list
    sql_error: bool

def setup_params_node(state: State, config=None) -> dict:
    """Initialize optimization parameters and constraints."""
    parameters = {
        "microcycle_days": 10,
        "workout_days": [1, 4, 7],
        "workout_types": [0, 1, 2],  # 0: Recovery, 1: Moderate, 2: Heavy
        "heavy_value": 2,
    }
    
    # Define all constraints with their active status
    constraints = {
        "same_workout_days_1_2": True,     # Days 1 and 2 must be same type
        "no_consecutive_heavy": True,       # No consecutive heavy days
        #uncomment to test infeasible constraint
       # "workout_1_is_heavy": True,         # The workout on day 1 is a heavy day
        "maximize_intensity": True          # Objective: maximize overall workout intensity
    }
    
    table_name = "exercise_library"

    return {
        "parameters": parameters,
        "constraints": constraints,
        "opt_model": None,
        "solution": None,
        "output": "",
        "logs": "Parameters and constraints initialized\n",
        "relaxation_attempts": [],
        "sql_query": f"SELECT name FROM {table_name}",
        "current_attempt": {
            "constraints": set(),
            "reasoning": None,
            "expected_impact": None
        }
    }

def execute_sql(state: State):
    possible_exercises = (
        db.session.query(
            Exercise_Library.name
        )
        .join(Exercise_Equipment, Exercise_Equipment.exercise_id == Exercise_Library.id)
        .join(Equipment_Library, Equipment_Library.id == Exercise_Equipment.equipment_id)
        .join(User_Equipment, User_Equipment.equipment_id == Equipment_Library.id)
        .filter(
            User_Equipment.user_id == current_user.id
        )
        .distinct()
        .group_by(Exercise_Library.name)
        .all()
    )

    for possible_exercise in possible_exercises:
        print(possible_exercise)

    '''
    completed_status_orders = (
        db.session.query(
            Payment_Types.payment_type_name,
            func.sum(Order_Cookies.quantity * Cookies.price).label("total_cost"),
        )
        .join(Orders, Orders.payment_id == Payment_Types.id)
        .join(Order_Cookies, Order_Cookies.order_id == Orders.id)
        .join(Cookies, Cookies.id == Order_Cookies.cookie_id)
        .filter(
            Orders.user_id == self.id,
            Orders.order_status_stored == "Complete",
        )
        .group_by(Payment_Types.payment_type_name)
        .all()
    )
    '''
    sql_query = state["sql_query"].strip()
    print(f"Executing SQL query: {sql_query}")
    try:
        result = db.session.execute(text(sql_query))
        if sql_query.lower().startswith("select"):
            rows = result.fetchall()
            columns = result.keys()
            if rows:
                header = ", ".join(columns)
                state["query_rows"] = [dict(zip(columns, row)) for row in rows]
                print(f"Raw SQL Query Result: {state['query_rows']}")
                # Format the result for readability
                data = ""
                #data = "; ".join([f"{row.get('food_name', row.get('name'))} for ${row.get('price', row.get('food_price'))}" for row in state["query_rows"]])
                for row in state["query_rows"]:
                    row_data = ""
                    for key, value in row.items():
                        row_data = row_data + f"{key}: {value}, "
                    data = data + row_data + "; "
                    print(data)
                formatted_result = f"{header}\n{data}"
            else:
                state["query_rows"] = []
                formatted_result = "No results found."
            state["query_result"] = formatted_result
            state["sql_error"] = False
            print("SQL SELECT query executed successfully.")
        else:
            db.session.commit()
            state["query_result"] = "The action has been successfully completed."
            state["sql_error"] = False
            print("SQL command executed successfully.")
    except Exception as e:
        state["query_result"] = f"Error executing SQL query: {str(e)}"
        state["sql_error"] = True
        print(f"Error executing SQL query: {str(e)}")
    return state


def build_opt_model_node(state: State, config=None) -> dict:
    """Build the optimization model with active constraints using PuLP."""
    params = state["parameters"]
    constraints = state["constraints"]
    
    num_days = params["microcycle_days"]
    workout_types = params["workout_types"]
    heavy = params["heavy_value"]
    max_val = max(workout_types)
    
    # Create the PuLP problem with the appropriate sense
    if constraints.get("maximize_intensity", False):
        prob = pulp.LpProblem("WorkoutSchedule", pulp.LpMaximize)
    else:
        prob = pulp.LpProblem("WorkoutSchedule", pulp.LpMinimize)
    
    # Decision Variables: workout_vars for each day (integer values between min and max workout types)
    workout_vars = [
        pulp.LpVariable(f'workout_day_{d}', lowBound=min(workout_types), upBound=max_val, cat=pulp.LpInteger)
        for d in range(num_days)
    ]
    
    # If "no_consecutive_heavy" is active, create binary variables to indicate heavy workouts
    is_heavy = None
    if constraints.get("no_consecutive_heavy", False):
        is_heavy = [pulp.LpVariable(f'is_heavy_{d}', cat=pulp.LpBinary) for d in range(num_days)]
        for d in range(num_days):
            # Link workout_vars and is_heavy:
            # If is_heavy[d] == 1 then workout_vars[d] must be heavy (== heavy),
            # and if is_heavy[d] == 0 then workout_vars[d] is forced to be at most heavy-1.
            prob += workout_vars[d] >= heavy * is_heavy[d], f"link_lower_{d}"
            prob += workout_vars[d] <= (heavy - 1) + is_heavy[d] * (max_val - (heavy - 1)), f"link_upper_{d}"
    
    state["logs"] += "\nBuilding model with constraints:\n"
    
    # Apply active constraints
    
    # Constraint: same_workout_days_1_2 forces day 1 and day 2 to be the same type
    if constraints.get("same_workout_days_1_2", False):
        prob += workout_vars[0] == workout_vars[1], "same_workout_days_1_2"
        state["logs"] += "- Days 1 and 2 must be same type\n"
    
    # Constraint: workout_1_is_heavy forces day 1 to be heavy
    if constraints.get("workout_1_is_heavy", False):
        prob += workout_vars[0] == heavy, "workout_1_is_heavy"
        state["logs"] += "- Day 1 must be heavy\n"
    
    # Constraint: no_consecutive_heavy prevents two consecutive heavy days using the binary indicators
    if constraints.get("no_consecutive_heavy", False) and is_heavy is not None:
        for d in range(num_days - 1):
            prob += is_heavy[d] + is_heavy[d+1] <= 1, f"no_consecutive_heavy_{d}"
        state["logs"] += "- No consecutive heavy days\n"
    
    # Objective: maximize_intensity maximizes the total intensity (sum of workout_vars)
    if constraints.get("maximize_intensity", False):
        prob += pulp.lpSum(workout_vars), "TotalIntensity"
        state["logs"] += "- Maximizing total intensity\n"
    
    return {"opt_model": (prob, workout_vars)}

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
    
    # Log LLM analysis
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
    """Solve model and record relaxation attempt results using PuLP."""
    prob, workout_vars = state["opt_model"]
    solver = pulp.PULP_CBC_CMD(msg=True)
    result_status = prob.solve(solver)
    
    status_str = pulp.LpStatus[prob.status]
    state["logs"] += f"\nSolver status: {status_str}\n"
    
    if status_str in ("Optimal", "Feasible"):
        schedule = [pulp.value(var) for var in workout_vars]
        total_intensity = sum(schedule)
        solution = {
            "schedule": schedule,
            "total_intensity": total_intensity,
            "status": status_str
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
        state["solution"] = solution
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
    state["solution"] = None
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
    builder.add_node("execute_sql", execute_sql)
    builder.add_node("build", build_opt_model_node)
    builder.add_node("solve", solve_model_node)
    builder.add_node("analyze", analyze_infeasibility_node)
    builder.add_node("format", format_solution_node)

    # Add edges
    builder.add_edge(START, "setup")
    #builder.add_edge("setup", "build")
    builder.add_edge("setup", "execute_sql")
    builder.add_edge("execute_sql", "build")
    builder.add_edge("build", "solve")

    def solution_router(state: State, config=None):
        if state["solution"] is None and any(state["constraints"].values()):
            return "analyze"  # Try relaxing a constraint
        return "format"      # Either a solution was found or no more constraints to relax

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

def Main():
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
        "sql_query": None,
        "current_attempt": {"constraints": set(), "reasoning": None, "expected_impact": None}
    }
    
    result = graph.invoke(initial_state)
    print(result["output"])
    return result

if __name__ == "__main__":
    Main()
