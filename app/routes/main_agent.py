from flask import request, jsonify, Blueprint, abort
from flask_login import login_required

bp = Blueprint('main_agent', __name__)

from app.main_agent.graph import create_main_agent_graph

# ----------------------------------------- Main Agent -----------------------------------------
test_cases = [
    "I want to train four times a week instead of three, and can we swap squats for leg press on leg day? I should have 30 minutes every day now.",
    "I'm switching jobs and won't be able to train on weekdays anymore. Let's shift to a strength phase this month.",
    "Over the next few months, I want to focus on cutting fat while maintaining muscle.",
    "I just moved and can now work out only on Monday, Wednesday, and Friday. My new goal is to build power over the next 12 weeks. Start with a strength block for 4 weeks, then move into a power phase. I want 3 full-body sessions a week. Let's include more explosive movements in each session.", 
    "Thanks, everything looks great for now.", 
    "Can we drop one hypertrophy session and add in some mobility work instead? Also, swap out overhead press for incline dumbbell press."
]



# Retrieve current user's main goal
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def change_macrocycle():
    # Input is a json.
    data = request.get_json()
    if not data:
        user_inputs = test_cases
    elif 'user_input' not in data:
        user_inputs = test_cases
    else:
        user_inputs = [data.get("user_input", "")]

    main_agent_app = create_main_agent_graph()

    # Invoke with new macrocycle and possible goal types.
    results = []
    for i, user_input in enumerate(user_inputs, start=1):
        state = main_agent_app.invoke({"user_input": user_input})
        state["iteration"] = i
        results.append(state)

    return jsonify({"status": "success", "states": results}), 200