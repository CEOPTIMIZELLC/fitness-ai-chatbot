from config import verbose
from flask import jsonify, Blueprint
from flask_login import current_user, login_required
from datetime import timedelta

from app import db
from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

from app.utils.common_table_queries import current_mesocycle, current_microcycle

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
    user_microcycles = User_Microcycles.query.join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=current_user.id).all()
    result = []
    for user_microcycle in user_microcycles:
        result.append(user_microcycle.to_dict())
    return jsonify({"status": "success", "microcycles": result}), 200

# Retrieve user's current mesocycle's microcycles
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_microcycles_list():
    result = []
    user_mesocycle = current_mesocycle(current_user.id)
    if not user_mesocycle:
        return jsonify({"status": "error", "message": "No active mesocycle found."}), 404
    user_microcycles = user_mesocycle.microcycles
    for user_microcycle in user_microcycles:
        result.append(user_microcycle.to_dict())
    return jsonify({"status": "success", "microcycles": result}), 200

# Retrieve user's current microcycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_microcycle():
    user_microcycle = current_microcycle(current_user.id)
    if not user_microcycle:
        return jsonify({"status": "error", "message": "No active microcycle found."}), 404
    return jsonify({"status": "success", "microcycles": user_microcycle.to_dict()}), 200


# Gives four microcycles for mesocycle.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def microcycle_initializer():

    user_mesocycle = current_mesocycle(current_user.id)
    if not user_mesocycle:
        return jsonify({"status": "error", "message": "No active mesocycle found."}), 404

    delete_old_user_microcycles(user_mesocycle.id)

    # Each microcycle must last 1 week.
    microcycle_duration = timedelta(weeks=1)

    # Find how many one week microcycles will be present in the mesocycle
    microcycle_count = user_mesocycle.duration.days // microcycle_duration.days

    microcycle_start = user_mesocycle.start_date

    microcycles = []

    # Create a microcycle for each week in the mesocycle.
    for i in range(microcycle_count):
        microcycle_end = microcycle_start + microcycle_duration
        new_microcycle = User_Microcycles(
            mesocycle_id = user_mesocycle.id,
            order = i+1,
            start_date = microcycle_start,
            end_date = microcycle_end,
        )

        microcycles.append(new_microcycle)

        # Shift the start of the next microcycle to be the end of the current.
        microcycle_start = microcycle_end

    db.session.add_all(microcycles)
    db.session.commit()

    result = []
    for microcycle in microcycles:
        result.append(microcycle.to_dict())
    return jsonify({"status": "success", "microcycles": result}), 200

