from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_required

bp = Blueprint('main_agent', __name__)

from config import agent_recursion_limit
from app import db
from app.models import User_Macrocycles, User_Weekday_Availability

from app.main_agent.graph import create_main_agent_graph

# ----------------------------------------- Main Agent -----------------------------------------
test_cases = [
    "I want to train four times a week instead of three, and can we swap squats for leg press on leg day? I should have 30 minutes every day now. My goal is to lose 20 pounds. I would like you to schedule the mesoscycles, microcycles, the phase components, and the workouts as well.",
    # "I want to train four times a week instead of three, and can we swap squats for leg press on leg day? I should have 30 minutes every day now.",
    "I want to train four times a week instead of three, and can we swap squats for leg press on leg day? I should have 30 minutes every day now. I would like you to schedule my mesocycles too.",
    "I'm switching jobs and won't be able to train on weekdays anymore. Let's shift to a strength phase this month.",
    "Over the next few months, I want to focus on cutting fat while maintaining muscle.",
    "I just moved and can now work out only on Monday, Wednesday, and Friday. My new goal is to build power over the next 12 weeks. Start with a strength block for 4 weeks, then move into a power phase. I want 3 full-body sessions a week. Let's include more explosive movements in each session.", 
    "Thanks, everything looks great for now.", 
    "Can we drop one hypertrophy session and add in some mobility work instead? Also, swap out overhead press for incline dumbbell press."
]

def run_main_agent(data):
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
        state = main_agent_app.invoke(
            {"user_input": user_input}, 
            config={
                "recursion_limit": agent_recursion_limit
            })
        state["iteration"] = i
        results.append(state)
    return results

def run_delete_schedules(user_id):
    db.session.query(User_Macrocycles).filter_by(user_id=user_id).delete()
    db.session.commit()
    db.session.query(User_Weekday_Availability).filter_by(user_id=user_id).delete()
    db.session.commit()
    results = f"Successfully deleted all schedules for user {user_id}."
    return results


# Test the main agent with a user input.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def test_main_agent():
    # Input is a json.
    data = request.get_json()
    results = run_main_agent(data)
    return jsonify({"status": "success", "states": results}), 200

# Delete all schedules belonging to the user.
@bp.route('/', methods=['DELETE'])
@login_required
def delete_schedules():
    results = run_delete_schedules(current_user.id)
    return jsonify({"status": "success", "states": results}), 200

# Test the main agent with a user input and no pre-existing data.
@bp.route('/clean', methods=['POST', 'PATCH'])
@login_required
def test_clean_main_agent():
    # Input is a json.
    data = request.get_json()
    run_delete_schedules(current_user.id)
    results = run_main_agent(data)
    return jsonify({"status": "success", "states": results}), 200