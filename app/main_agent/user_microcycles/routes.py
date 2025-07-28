from flask import jsonify, Blueprint
from flask_login import login_required, current_user

from app.main_agent.user_microcycles import create_microcycle_agent

from app.utils.alter_json_dict import recursively_change_dict_timedeltas

bp = Blueprint('user_microcycles', __name__)

# ----------------------------------------- User Microcycles -----------------------------------------

# Retrieve current user's microcycles
@bp.route('/', methods=['GET'])
@login_required
def get_user_microcycles_list():
    state = {
        "user_id": current_user.id,
        "microcycle_impacted": True,
        "microcycle_is_altered": False,
        "microcycle_read_plural": True,
        "microcycle_read_current": False,
        "microcycle_message": "Perform microcycle scheduling."
    }
    microcycle_agent = create_microcycle_agent()

    result = microcycle_agent.invoke(state)

    return jsonify({"status": "success", "microcycles": result}), 200

# Retrieve user's current macrocycle's mesocycles
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_mesocycles_list():
    state = {
        "user_id": current_user.id,
        "microcycle_impacted": True,
        "microcycle_is_altered": False,
        "microcycle_read_plural": True,
        "microcycle_read_current": True,
        "microcycle_message": "Perform microcycle scheduling."
    }
    microcycle_agent = create_microcycle_agent()

    result = microcycle_agent.invoke(state)

    return jsonify({"status": "success", "microcycles": result}), 200

# Retrieve user's current microcycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_microcycle():
    state = {
        "user_id": current_user.id,
        "microcycle_impacted": True,
        "microcycle_is_altered": False,
        "microcycle_read_plural": False,
        "microcycle_read_current": True,
        "microcycle_message": "Perform microcycle scheduling."
    }
    microcycle_agent = create_microcycle_agent()

    result = microcycle_agent.invoke(state)

    return jsonify({"status": "success", "microcycles": result}), 200

# Gives four microcycles for mesocycle.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def microcycle_initializer():
    state = {
        "user_id": current_user.id,
        "microcycle_impacted": True,
        "microcycle_is_altered": True,
        "microcycle_read_plural": False,
        "microcycle_read_current": False,
        "microcycle_message": "Perform microcycle scheduling."
    }
    microcycle_agent = create_microcycle_agent()

    result = microcycle_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"status": "success", "microcycles": result}), 200

# Gives four microcycles for mesocycle and gives the parent mesocycle a new id.
@bp.route('/<phase_id>', methods=['POST', 'PATCH'])
@login_required
def microcycle_initializer_by_id(phase_id):
    state = {
        "user_id": current_user.id,
        "microcycle_impacted": True,
        "microcycle_is_altered": True,
        "microcycle_read_plural": False,
        "microcycle_read_current": False,
        "microcycle_message": "Perform microcycle scheduling.",
        "microcycle_perform_with_parent_id": phase_id
    }
    microcycle_agent = create_microcycle_agent()

    result = microcycle_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"status": "success", "microcycles": result}), 200