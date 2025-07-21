from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_required

from app import db
from app.models import Weekday_Library, User_Weekday_Availability

from app.agents.weekday_availability import create_weekday_availability_extraction_graph
from app.main_agent.user_weekdays_availability import create_availability_agent, WeekdayAvailabilitySchedulerActions

from .utils import recursively_change_dict_timedeltas

bp = Blueprint('user_weekday_availability', __name__)

# ----------------------------------------- User Weekday Availability -----------------------------------------
# Retrieve possible weekday types.
def retrieve_weekday_types():
    weekdays = (
        db.session.query(
            Weekday_Library.id,
            Weekday_Library.name
        )
        .all()
    )

    return [
        {
            "id": weekday.id, 
            "name": weekday.name.lower()
        } 
        for weekday in weekdays
    ]

# Retrieve current user's weekdays
@bp.route('/', methods=['GET'])
@login_required
def get_user_weekday_list():
    state = {
        "user_id": current_user.id,
        "availability_impacted": True,
        "availability_is_altered": False,
        "availability_read_plural": True,
        "availability_read_current": True,
        "availability_message": "Retrieve current availability"
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
        "availability_impacted": True,
        "availability_is_altered": False,
        "availability_read_plural": False,
        "availability_read_current": True,
        "availability_message": "Retrieve current availability"
    }
    availability_agent = create_availability_agent()

    result = availability_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)
    return jsonify({"status": "success", "weekdays": result}), 200

# Retrieve current user's weekdays formatted
@bp.route('/current_formatted_list', methods=['GET'])
@login_required
def get_user_weekday_formatted_list():
    state = {
        "user_id": current_user.id,
        "availability_impacted": True,
        "availability_is_altered": False,
        "availability_read_plural": True,
        "availability_read_current": True,
        "availability_message": "Retrieve current availability"
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
        "availability_impacted": True,
        "availability_is_altered": True,
        "availability_read_plural": False,
        "availability_read_current": False,
        "availability_message": data.get("availability", "")
    }
    availability_agent = create_availability_agent()

    result = availability_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"weekdays": result}), 200