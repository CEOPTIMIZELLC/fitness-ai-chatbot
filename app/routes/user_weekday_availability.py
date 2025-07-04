from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_required

from app import db
from app.models import Weekday_Library, User_Weekday_Availability

from app.agents.weekday_availability import create_weekday_availability_extraction_graph
from app.main_agent.user_weekdays_availability import WeekdayAvailabilitySchedulerActions

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
    weekdays = WeekdayAvailabilitySchedulerActions.get_user_list()
    return jsonify({"status": "success", "weekdays": weekdays}), 200

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

    state = WeekdayAvailabilitySchedulerActions.scheduler(data.get("availability", ""))

    return jsonify({
        "new_availability": state["new_availability"]
    }), 200