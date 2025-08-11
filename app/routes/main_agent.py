from logging_config import log_verbose

from flask import request, jsonify, Blueprint, current_app, abort
from flask_login import current_user, login_required

bp = Blueprint('main_agent', __name__)

from config import agent_recursion_limit
from app import db
from app.models import User_Macrocycles, User_Weekday_Availability

from app.main_agent.graph import create_main_agent_graph
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt, Command

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

# Deletes all current schedule items and availabilities for the current user.
def run_delete_schedules(user_id):
    db.session.query(User_Macrocycles).filter_by(user_id=user_id).delete()
    db.session.commit()
    db.session.query(User_Weekday_Availability).filter_by(user_id=user_id).delete()
    db.session.commit()
    results = f"Successfully deleted all schedules for user {user_id}."
    return results

# Enters the main agent.
def enter_main_agent(user_id, delete_old_schedules=False):
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    # 👇 keep checkpointer alive during invocation
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        main_agent_app = create_main_agent_graph(checkpointer=checkpointer)
        
        thread = {"configurable": {"thread_id": f"user-{user_id}"}}

        # Invoke with new macrocycle and possible goal types.
        if delete_old_schedules:
            run_delete_schedules(user_id)
        result = main_agent_app.invoke(
            {"user_id": user_id}, 
            config={
                "recursion_limit": agent_recursion_limit,
                "configurable": {
                    "thread_id": f"user-{user_id}",
                }
            })

        # Retrieve the current state of the agent.
        snapshot_of_agent = main_agent_app.get_state(thread)

        # Retrieve the current interrupt, if there is one.
        tasks = snapshot_of_agent.tasks
        if tasks:
            interrupt_message = snapshot_of_agent.tasks[0].interrupts[0].value["task"]
            log_verbose(f"Interrupt: {interrupt_message}")
    return snapshot_of_agent

# Resumes the main agent with user input.
def resume_main_agent(user_id, data):
    if (not data) or ('user_input' not in data):
        abort(400, description="No update given.")
    else:
        user_input = data.get("user_input", "")

    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    # 👇 keep checkpointer alive during invocation
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        main_agent_app = create_main_agent_graph(checkpointer=checkpointer)
        
        thread = {"configurable": {"thread_id": f"user-{user_id}"}}
        snapshot_of_agent = main_agent_app.get_state(thread)

        result = main_agent_app.invoke(
            Command(resume={"user_input": user_input}),
            config=snapshot_of_agent.config
        )

        # Retrieve the current state of the agent.
        snapshot_of_agent = main_agent_app.get_state(thread)

        # Retrieve the current interrupt, if there is one.
        tasks = snapshot_of_agent.tasks
        if tasks:
            interrupt_message = snapshot_of_agent.tasks[0].interrupts[0].value["task"]
            log_verbose(f"Interrupt: {interrupt_message}")
    return snapshot_of_agent

# Enter into the main agent with a user input.
@bp.route('/enter', methods=['POST', 'PATCH'])
@login_required
def test_enter_main_agent():
    user_id = current_user.id
    results = enter_main_agent(user_id)
    return jsonify({"status": "success", "states": results}), 200

# Enter the main agent with a user input and no pre-existing data.
@bp.route('/clean_enter', methods=['POST', 'PATCH'])
@login_required
def test_clean_enter_main_agent():
    user_id = current_user.id
    results = enter_main_agent(user_id, delete_old_schedules=True)
    return jsonify({"status": "success", "states": results}), 200


# Resumes the main agent with a user input.
@bp.route('/resume', methods=['POST', 'PATCH'])
@login_required
def test_resume_main_agent():
    # Input is a json.
    data = request.get_json()
    user_id = current_user.id
    results = resume_main_agent(user_id, data)
    return jsonify({"status": "success", "states": results}), 200

# Enter the main agent and test it with a user input.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def test_main_agent():
    # Input is a json.
    data = request.get_json()
    user_id = current_user.id
    results = enter_main_agent(user_id)
    results = resume_main_agent(user_id, data)
    return jsonify({"status": "success", "states": results}), 200

# Enter the main agent and test it with a user input and no pre-existing data.
@bp.route('/clean', methods=['POST', 'PATCH'])
@login_required
def test_clean_main_agent():
    # Input is a json.
    data = request.get_json()
    user_id = current_user.id
    results = enter_main_agent(user_id, delete_old_schedules=True)
    results = resume_main_agent(user_id, data)
    return jsonify({"status": "success", "states": results}), 200

# Delete all schedules belonging to the user.
@bp.route('/', methods=['DELETE'])
@login_required
def delete_schedules():
    results = run_delete_schedules(current_user.id)
    return jsonify({"status": "success", "states": results}), 200

# Retrieve current state.
@bp.route('/state', methods=['GET'])
@login_required
def get_current_state():
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    # 👇 keep checkpointer alive during invocation
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        main_agent_app = create_main_agent_graph(checkpointer=checkpointer)
        
        thread = {"configurable": {"thread_id": f"user-{current_user.id}"}}

        snapshot_of_agent = main_agent_app.get_state(thread)

    return jsonify({"status": "success", "agent_snapshot": snapshot_of_agent}), 200