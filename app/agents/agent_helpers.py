from langchain_openai import ChatOpenAI

def find_constraints_on_variable(model_proto, agent_var):
    var_index = agent_var.Index()
    constraints_on_var = []

    for constraint_proto in model_proto.constraints:
        if ((constraint_proto.HasField("linear") and var_index in constraint_proto.linear.agent_vars) or 
            (constraint_proto.HasField("bool_or") and var_index in constraint_proto.bool_or.literals) or 
            (constraint_proto.HasField("interval") and (var_index == constraint_proto.interval.start or 
                                                        var_index == constraint_proto.interval.size or 
                                                        var_index == constraint_proto.interval.end)) or 
            (constraint_proto.HasField("bool_and") and var_index in constraint_proto.bool_and.literals) or 
            (constraint_proto.HasField("at_most_one") and var_index in constraint_proto.at_most_one.literals) or 
            # (constraint_proto.HasField("at_least_one") and var_index in constraint_proto.at_least_one.literals) or 
            (constraint_proto.HasField("exactly_one") and var_index in constraint_proto.exactly_one.literals) or 
            # (constraint_proto.HasField("int_max") and (var_index == constraint_proto.int_max.target or var_index in constraint_proto.int_max.agent_vars)) or 
            # (constraint_proto.HasField("int_min") and (var_index == constraint_proto.int_min.target or var_index in constraint_proto.int_min.agent_vars)) or 
            (constraint_proto.HasField("int_div") and (var_index in constraint_proto.int_div.target.agent_vars or 
                                                       any(var_index in exprs.agent_vars for exprs in constraint_proto.int_div.exprs))) or 
            (constraint_proto.HasField("int_mod") and (var_index == constraint_proto.int_mod.target or 
                                                       var_index == constraint_proto.int_mod.agent_var or 
                                                       var_index == constraint_proto.int_mod.modulus)) or 
            (constraint_proto.HasField("int_prod") and (var_index in constraint_proto.int_prod.target.agent_vars or 
                                                       any(var_index in exprs.agent_vars for exprs in constraint_proto.int_prod.exprs))) or 
            (constraint_proto.HasField("circuit") and (var_index in constraint_proto.circuit.tails or 
                                                       var_index in constraint_proto.circuit.heads or 
                                                       (constraint_proto.circuit.literals and var_index in constraint_proto.circuit.literals))) or 
            (constraint_proto.HasField("routes") and (var_index in constraint_proto.routes.tails or 
                                                      var_index in constraint_proto.routes.heads or 
                                                      var_index in constraint_proto.routes.demands or 
                                                      var_index == constraint_proto.routes.cost)) or 
            # (constraint_proto.HasField("diffn") and any(var_index in shape.agent_vars for box in constraint_proto.diffn.boxes for shape in [box.x_size, box.y_size, box.z_size] if shape.agent_vars)) or 
            (constraint_proto.HasField("cumulative") and (
                (var_index in constraint_proto.cumulative.capacities) or 
                any(var_index in interval.agent_vars 
                    for interval in constraint_proto.cumulative.intervals 
                    for var_index in [interval.start, interval.size, interval.end]))) or 
            (constraint_proto.HasField("table") and var_index in constraint_proto.table.agent_vars) or 
            (constraint_proto.HasField("automaton") and (var_index in constraint_proto.automaton.agent_vars or 
                                                         var_index in constraint_proto.automaton.transition_vars)) or 
            (constraint_proto.HasField("inverse") and (var_index in constraint_proto.inverse.f_direct or 
                                                       var_index in constraint_proto.inverse.f_inverse)) or 
            (constraint_proto.HasField("element") and (var_index == constraint_proto.element.target or 
                                                       var_index == constraint_proto.element.index or 
                                                       var_index in constraint_proto.element.agent_vars))):
            constraints_on_var.append(constraint_proto)
    return constraints_on_var


def retrieve_relaxation_history(relaxation_attempts):
    """Prepare the history of each relaxation attempt made."""
    history = []
    for attempt in relaxation_attempts:
        result = "successful" if attempt.result_feasible else "unsuccessful"
        history.append(
            f"Relaxed {attempt.constraints_relaxed}: {result}\n"
            f"Reasoning: {attempt.reasoning}\n"
            f"Impact: {attempt.expected_impact}\n"
        )
    return history

def analyze_infeasibility(state, history, available_constraints) -> dict:
    """Use LLM to analyze solver logs and suggest constraints to relax."""
    model = ChatOpenAI(temperature=0)

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

Available constraints: {available_constraints}

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
    
    return state