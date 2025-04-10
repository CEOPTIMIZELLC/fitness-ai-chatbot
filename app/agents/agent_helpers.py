from langchain_openai import ChatOpenAI

def longest_string_size_for_key(items, key):
    return len(max(items, key=lambda d:len(d[key]))[key])

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