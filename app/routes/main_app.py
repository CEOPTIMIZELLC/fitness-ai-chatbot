import json

from flask import request, Blueprint, abort, Response, stream_with_context
from flask_login import current_user, login_required

bp = Blueprint('main_app', __name__)

from app.actions import resume_main_agent

# ----------------------------------------- Main Agent -----------------------------------------

# Method to retrieve the user input for the user.
def retrieve_user_input_from_json_input(data):
    if not data:
        abort(404, description="Invalid request")

    if ("message" not in data) and ("user_input" not in data):
        abort(400, description="No update given.")

    else:
        user_input = data.get("message", data.get("user_input", ""))
    return user_input

def _sse_event(event_type: str, payload: dict) -> str:
    """
    Formats a single Server-Sent-Event line with JSON payload.
    We keep it minimal and newline-delimited for robust streaming over fetch().
    """
    # Standard SSE: "event:" and "data:" lines ending with double newline
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

# New: Streaming endpoint that emits progress / interrupt / final
@bp.route('/resume', methods=['POST'])
@login_required
def main_resume():
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
