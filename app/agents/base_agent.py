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

    def analyze_infeasibility_node(self, state: TState, config=None) -> dict:
        """Use LLM to analyze solver logs and suggest constraints to relax."""
        # Prepare history of what's been tried
        history = retrieve_relaxation_history(state["relaxation_attempts"])
        state = analyze_infeasibility(state, history, self.available_constraints)

        return {
            "constraints": state["constraints"],
            "current_attempt": state["current_attempt"]
        }

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


    def format_constraint_status(self, constraints: dict) -> str:
        """Format the final constraint status section."""
        formatted = "\nFinal Constraint Status:\n"
        for constraint, active in constraints.items():
            formatted += f"- {constraint}: {'Active' if active else 'Relaxed'}\n"
        return formatted