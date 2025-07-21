from config import verbose
from flask import jsonify, Blueprint
from flask_login import login_required, current_user
from datetime import timedelta

from app import db
from app.models import User_Microcycles
from app.main_agent.user_microcycles import create_microcycle_agent, MicrocycleActions

bp = Blueprint('user_microcycles', __name__)

# ----------------------------------------- User Microcycles -----------------------------------------

def delete_old_user_microcycles(mesocycle_id):
    db.session.query(User_Microcycles).filter_by(mesocycle_id=mesocycle_id).delete()
    if verbose:
        print("Successfully deleted")

# Retrieve current user's microcycles
@bp.route('/', methods=['GET'])
@login_required
def get_user_microcycles_list():
    microcycles = MicrocycleActions.get_user_list()
    return jsonify({"status": "success", "microcycles": microcycles}), 200

# Retrieve user's current mesocycle's microcycles
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_microcycles_list():
    microcycles = MicrocycleActions.get_user_current_list()
    return jsonify({"status": "success", "microcycles": microcycles}), 200

# Retrieve user's current microcycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_microcycle():
    microcycles = MicrocycleActions.read_user_current_element()
    return jsonify({"status": "success", "microcycles": microcycles}), 200

# Gives four microcycles for mesocycle.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def microcycle_initializer():
    state = {
        "user_id": current_user.id,
        "microcycle_impacted": True,
        "microcycle_message": "Perform microcycle scheduling."
    }
    microcycle_agent = create_microcycle_agent()

    result = microcycle_agent.invoke(state)

    # Correct time delta for serializing for JSON output.
    for key, value in result.items():
        if isinstance(value, timedelta):
            result[key] = str(value)

    return jsonify({"status": "success", "microcycles": result}), 200

