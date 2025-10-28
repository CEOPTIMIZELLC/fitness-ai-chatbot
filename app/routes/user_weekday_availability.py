from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_required

from app.main_sub_agents.user_weekdays_availability import create_availability_agent as create_agent

from app.utils.item_to_string import recursively_change_dict_timedeltas

bp = Blueprint('user_weekday_availability', __name__)

from .blueprint_factories import get_user_current_list, read_user_current, item_initializer

# ----------------------------------------- User Weekday Availability -----------------------------------------

# Retrieve current user's weekdays
@bp.route('/', methods=['GET'])
@login_required
def get_user_weekday_list():
    return get_user_current_list(focus_name="availability", agent_creation_caller=create_agent)

# Retrieve current user's weekdays formatted
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_weekday_current_list():
    return get_user_current_list(focus_name="availability", agent_creation_caller=create_agent)

# Retrieve user's current microcycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_weekday():
    return read_user_current(focus_name="availability", agent_creation_caller=create_agent)

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

    return item_initializer(focus_name="availability", agent_creation_caller=create_agent, user_message=data.get("availability", ""))