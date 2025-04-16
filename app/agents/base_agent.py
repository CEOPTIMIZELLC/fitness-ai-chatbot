from typing_extensions import TypedDict, TypeVar
from langgraph.graph import StateGraph, START, END
from app.agents.agent_helpers import retrieve_relaxation_history, analyze_infeasibility

from datetime import datetime
from typing import Set, Optional


class BaseRelaxationAttempt:
    def __init__(self, 
                 constraints_relaxed: Set[str], 
                 result_feasible: bool, 
                 reasoning: Optional[str] = None, 
                 expected_impact: Optional[str] = None):
        self.constraints_relaxed = set(constraints_relaxed)
        self.result_feasible = result_feasible
        self.timestamp = datetime.now()
        self.reasoning = reasoning
        self.expected_impact = expected_impact

class BaseAgentState(TypedDict):
    parameters: dict
    constraints: dict
    opt_model: any
    solution: any
    formatted: str
    output: list
    logs: str
    relaxation_attempts: list
    current_attempt: dict

# Create a generic type variable that must be a subclass of BaseAgentState
TState = TypeVar('TState', bound=BaseAgentState)

class BaseAgent:
    # Each child class should override this with their specific constraints
    available_constraints = ""

    def __init__(self):
        self.initial_state = {
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

    def _format_duration(self, seconds: int) -> str:
        """Format duration in minutes and seconds"""
        return f"{seconds // 60} min {seconds % 60} sec ({seconds} sec)"

    def _format_range(self, value, min_val, max_val) -> str:
        """Format a value with its allowed range"""
        return f"{value} ({min_val}-{max_val})"

    def _create_formatted_field(self, label: str, value: str, header_length: int) -> str:
        """Helper method to create consistently formatted fields"""
        prefix = "| " if label != "#" else ""
        formatted = f"{prefix}{value}"
        return f"{formatted:<{header_length}}"

    def analyze_infeasibility_node(self, state: TState, config=None) -> dict:
        """Use LLM to analyze solver logs and suggest constraints to relax."""
        # Prepare history of what's been tried
        history = retrieve_relaxation_history(state["relaxation_attempts"])
        state = analyze_infeasibility(state, history, self.available_constraints)

        return {
            "constraints": state["constraints"],
            "current_attempt": state["current_attempt"]
        }

    def format_relaxation_attempts(self, relaxation_attempts, formatted, *args):
        """Format the relaxation attempts history."""
        formatted += "Relaxation Attempts:\n"
        formatted += "-" * 40 + "\n"
        for i, attempt in enumerate(relaxation_attempts, 1):
            formatted += f"\nAttempt {i}:\n"
            formatted += f"Constraints relaxed: {attempt.constraints_relaxed}\n"
            formatted += f"Result: {'Feasible' if attempt.result_feasible else 'Infeasible'}\n"

            formatted = self.format_class_specific_relaxation_history(formatted, attempt, *args)

            if attempt.reasoning:
                formatted += f"Reasoning: {attempt.reasoning}\n"
            if attempt.expected_impact:
                formatted += f"Expected Impact: {attempt.expected_impact}\n"
            formatted += f"Timestamp: {attempt.timestamp}\n"
        return formatted

    def format_constraint_status(self, constraints: dict) -> str:
        """Format the final constraint status section."""
        formatted = "\nFinal Constraint Status:\n"
        for constraint, active in constraints.items():
            formatted += f"- {constraint}: {'Active' if active else 'Relaxed'}\n"
        return formatted

    def format_solution_node(self, state: TState, config=None) -> dict:
        """Format the optimization results."""
        solution, parameters = state["solution"], state["parameters"]
        
        # Get parameters specific to each formatter
        relaxation_attempts_args = self.get_relaxation_formatting_parameters(parameters)
        agent_output_args = self.get_model_formatting_parameters(parameters)
        
        formatted = "Optimization Results:\n"
        formatted += "=" * 50 + "\n\n"

        # Show relaxation attempts history
        formatted = self.format_relaxation_attempts(state["relaxation_attempts"], formatted, *relaxation_attempts_args)

        if solution is None:
            final_output = []
            formatted += "\nNo valid schedule found even with relaxed constraints.\n"
        else:
            schedule = solution["schedule"]
            final_output, formatted = self.format_agent_output(solution, formatted, schedule, *agent_output_args)

            # Show final constraint status
            formatted += self.format_constraint_status(state["constraints"])

        return {"formatted": formatted, "output": final_output}

    def create_optimization_graph(self, state_class: type[TState]):
        builder = StateGraph(state_class)

        # Add common nodes
        builder.add_node("setup", self.setup_params_node)
        builder.add_node("build", self.build_opt_model_node)
        builder.add_node("solve", self.solve_model_node)
        builder.add_node("analyze", self.analyze_infeasibility_node)
        builder.add_node("format", self.format_solution_node)

        # Add common edges
        builder.add_edge(START, "setup")
        builder.add_edge("setup", "build")
        builder.add_edge("build", "solve")

        builder.add_conditional_edges(
            "solve",
            self.solution_router,
            {
                "analyze": "analyze",
                "format": "format"
            }
        )

        builder.add_edge("analyze", "build")
        builder.add_edge("format", END)

        return builder.compile()

    def solution_router(self, state: TState, config=None):
        if state["solution"] is None and any(state["constraints"].values()):
            return "analyze"
        return "format"

    def run(self, parameter_input=None):
        # This will be overridden by child classes to provide their specific state class
        raise NotImplementedError("Child classes must implement run()")