from typing_extensions import TypedDict, TypeVar
from langgraph.graph import StateGraph, START, END

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

