from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_required

from app.main_sub_agents.user_weekdays_availability import create_availability_agent

from app.utils.item_to_string import recursively_change_dict_timedeltas

bp = Blueprint('user_weekday_availability', __name__)

# ----------------------------------------- User Weekday Availability -----------------------------------------

# Retrieve current user's weekdays
@bp.route('/', methods=['GET'])
@login_required
def get_user_weekday_list():
    state = {
        "user_id": current_user.id,
        "availability_is_requested": True,
        "availability_is_alter": False,
        "availability_is_read": True,
        "availability_read_plural": True,
        "availability_read_current": True,
        "availability_detail": "Retrieve current availability"
    }
    availability_agent = create_availability_agent()

    result = availability_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)
    return jsonify({"status": "success", "weekdays": result}), 200

# Retrieve current user's weekdays formatted
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_weekday_current_list():
    state = {
        "user_id": current_user.id,
        "availability_is_requested": True,
        "availability_is_alter": False,
        "availability_is_read": True,
        "availability_read_plural": True,
        "availability_read_current": True,
        "availability_detail": "Retrieve current availability"
    }
    availability_agent = create_availability_agent()

    result = availability_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)
    return jsonify({"status": "success", "weekdays": result}), 200

# Retrieve user's current microcycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_weekday():
    state = {
        "user_id": current_user.id,
        "availability_is_requested": True,
        "availability_is_alter": False,
        "availability_is_read": True,
        "availability_read_plural": False,
        "availability_read_current": True,
        "availability_detail": "Retrieve current availability"
    }
    availability_agent = create_availability_agent()

    result = availability_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)
    return jsonify({"status": "success", "weekdays": result}), 200

# Change the current user's weekday.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def change_weekday_availability():
    # Input is a json.
    data = request.get_json()
    if not data:
        abort(404, description="Invalid request")
    
    if ('availability' not in data):
        abort(400, description="Please fill out the form!")

    state = {
        "user_id": current_user.id,
        "availability_is_requested": True,
        "availability_is_alter": True,
        "availability_is_read": True,
        "availability_read_plural": False,
        "availability_read_current": False,
        "availability_detail": data.get("availability", "")
    }
    availability_agent = create_availability_agent()

    result = availability_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"weekdays": result}), 200