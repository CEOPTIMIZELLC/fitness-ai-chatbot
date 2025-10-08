import json

from flask import request, jsonify, Blueprint, current_app, abort, Response, stream_with_context
from flask_login import current_user, login_required

bp = Blueprint('main_agent', __name__)

from langgraph.checkpoint.postgres import PostgresSaver

from app import db
from app.models import User_Macrocycles, User_Weekday_Availability

from app.graph import create_main_agent_graph
from app.actions import enter_main_agent, resume_main_agent

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

# Method to retrieve the user input for the user.
def retrieve_user_input_from_json_input(data):
    if not data:
        abort(404, description="Invalid request")

    if ("message" not in data) and ("user_input" not in data):
        abort(400, description="No update given.")

    else:
        user_input = data.get("message", data.get("user_input", ""))
    return user_input

# Deletes all current schedule items and availabilities for the current user.
def run_delete_schedules(user_id):
    db.session.query(User_Macrocycles).filter_by(user_id=user_id).delete()
    db.session.commit()
    db.session.query(User_Weekday_Availability).filter_by(user_id=user_id).delete()
    db.session.commit()
    results = f"Successfully deleted all schedules for user {user_id}."
    return results

# Enter into the main agent with a user input.
@bp.route('/enter', methods=['POST', 'PATCH'])
@login_required
def test_enter_main_agent(delete_all_user_schedules=False):
    user_id = current_user.id

    # If deletion is desired, remove all previous schedule and availabilities.
    if delete_all_user_schedules:
        run_delete_schedules(user_id)

    # Results of the inital agent entry.
    snapshot_of_agent, interrupt_messages = enter_main_agent(user_id)
    return jsonify({"status": "success", "response": interrupt_messages}), 200

# Enter the main agent with a user input and no pre-existing data.
@bp.route('/enter/clean', methods=['POST', 'PATCH'])
@login_required
def test_enter_main_agent_clean():
    return test_enter_main_agent(delete_all_user_schedules=True)

# Resumes the main agent with a user input.
@bp.route('/resume', methods=['POST', 'PATCH'])
@login_required
def test_resume_main_agent():
    user_id = current_user.id

    # Input is a json.
    data = request.get_json()
    user_input = retrieve_user_input_from_json_input(data)

    # Results of the user input.
    snapshot_of_agent, interrupt_messages = resume_main_agent(user_id, user_input)
    return jsonify({"status": "success", "response": interrupt_messages}), 200

# Exit the Main Agent.
@bp.route('/exit', methods=['POST', 'PATCH'])
@login_required
def test_exit_main_agent():
    user_id = current_user.id

    # Results of the user input.
    snapshot_of_agent, interrupt_messages = resume_main_agent(user_id, "")
    return jsonify({"status": "success", "response": interrupt_messages}), 200

# Enter the main agent and test it with a user input.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def test_main_agent(delete_all_user_schedules=False):
    user_id = current_user.id

    # If deletion is desired, remove all previous schedule and availabilities.
    if delete_all_user_schedules:
        run_delete_schedules(user_id)

    # Results of the inital agent entry.
    snapshot_of_agent, interrupt_messages = enter_main_agent(user_id)

    # Input is a json.
    data = request.get_json()
    user_input = retrieve_user_input_from_json_input(data)

    # Results of the user input.
    snapshot_of_agent, interrupt_messages = resume_main_agent(user_id, user_input)
    return jsonify({"status": "success", "response": interrupt_messages}), 200

# Enter the main agent and test it with a user input and no pre-existing data.
@bp.route('/clean', methods=['POST', 'PATCH'])
@login_required
def test_main_agent_clean():
    return test_main_agent(delete_all_user_schedules=True)

# Delete all schedules belonging to the user.
@bp.route('/', methods=['DELETE'])
@login_required
def delete_schedules():
    results = run_delete_schedules(current_user.id)
    return jsonify({"status": "success", "response": results}), 200

# Retrieve current state.
@bp.route('/state', methods=['GET'])
@login_required
def get_current_state():
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    # Keep checkpointer alive during invocation
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        main_agent_app = create_main_agent_graph(checkpointer=checkpointer)
        
        thread = {"configurable": {"thread_id": f"user-{current_user.id}"}}

        snapshot_of_agent = main_agent_app.get_state(thread)

    return jsonify({"status": "success", "response": snapshot_of_agent}), 200

def _sse_event(event_type: str, payload: dict) -> str:
    """
    Formats a single Server-Sent-Event line with JSON payload.
    We keep it minimal and newline-delimited for robust streaming over fetch().
    """
    # Standard SSE: "event:" and "data:" lines ending with double newline
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

# New: Streaming endpoint that emits progress / interrupt / final
@bp.route('/resume_stream', methods=['POST'])
@login_required
def resume_stream():
    user_id = current_user.id
    data = request.get_json()
    user_input = retrieve_user_input_from_json_input(data)

    # Call your agent. If this later becomes a generator, you can yield directly here.
    progress_messages, interrupt_messages = resume_main_agent(user_id, user_input)

    @stream_with_context
    def generate():
        # 1) Stream progress messages (continue after each)
        for msg in (progress_messages or []):
            yield _sse_event("progress", {"message": msg})

        # 2) If any interrupt messages, stream the first (or all) and stop
        if interrupt_messages:
            for msg in interrupt_messages:
                yield _sse_event("interrupt", {"message": msg})
            return  # stop streaming; frontend will wait for new user input

        # 3) Otherwise, signal final completion
        yield _sse_event("final", {"message": "Task completed."})

    # Use an SSE content type for robust streaming over fetch()
    return Response(generate(), mimetype="text/event-stream")
