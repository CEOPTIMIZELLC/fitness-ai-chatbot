from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Goal_Library, Goal_Phase_Requirements, Phase_Library, User_Microcycles, User_Mesocycles, User_Macrocycles
from datetime import datetime, timedelta

bp = Blueprint('user_microcycles', __name__)

from app.agents.phases import Main as phase_main
from app.helper_functions.common_table_queries import current_macrocycle, current_mesocycle, current_microcycle

# ----------------------------------------- Phases -----------------------------------------

def delete_old_user_phases(mesocycle_id):
    db.session.query(User_Microcycles).filter_by(mesocycle_id=mesocycle_id).delete()
    print("Successfully deleted")

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_phase_constraints_for_goal(goal_id):
    # Retrieve all possible phases that can be selected.
    possible_phases = (
        db.session.query(
            Phase_Library.id,
            Phase_Library.name,
            Phase_Library.phase_duration_minimum_in_weeks,
            Phase_Library.phase_duration_maximum_in_weeks,
            Goal_Phase_Requirements.required_phase,
            Goal_Phase_Requirements.is_goal_phase,
        )
        .join(Goal_Phase_Requirements, Goal_Phase_Requirements.phase_id == Phase_Library.id)
        .join(Goal_Library, Goal_Library.id == Goal_Phase_Requirements.goal_id)
        .filter(Goal_Library.id == goal_id)
        .order_by(Phase_Library.id.asc())
        .all()
    )
    return possible_phases


# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_current_mesocycle():
    from datetime import date
    today = date.today()
    # Retrieve all possible phases that can be selected.
    current_mesocyle = (
        db.session.query(
            User_Mesocycles.id,
            User_Mesocycles.macrocycle_id,
            User_Mesocycles.phase_id,
            User_Mesocycles.order,
            User_Mesocycles.start_date,
            User_Mesocycles.end_date,
        )
        .join(User_Macrocycles, User_Macrocycles.id == User_Mesocycles.macrocycle_id)
        .filter(
            User_Mesocycles.start_date <= today, 
            User_Mesocycles.end_date >= today,
            User_Macrocycles.user_id == current_user.id,
            )
        .order_by(User_Mesocycles.id.desc())
        .first()
    )
    return current_mesocyle

# Retrieve phases
@bp.route('/', methods=['GET'])
@login_required
def get_user_microcycles():
    user_microcycles = User_Microcycles.query.join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=current_user.id).all()
    result = []
    for user_microcycle in user_microcycles:
        result.append(user_microcycle.to_dict())
    return jsonify({"status": "success", "phases": result}), 200

# Retrieve phases
@bp.route('/current_mesocycle', methods=['GET'])
@login_required
def get_user_current_microcycles():
    result = []
    user_mesocycle = current_mesocycle(current_user.id)
    user_microcycles = user_mesocycle.microcycles
    for user_microcycle in user_microcycles:
        result.append(user_microcycle.to_dict())
    return jsonify({"status": "success", "microcycles": result}), 200

# Retrieve user's current phase
@bp.route('/current', methods=['GET'])
@login_required
def get_user_current_microcycle():
    user_microcycle = current_microcycle(current_user.id)
    if not user_microcycle:
        return jsonify({"status": "error", "message": "No active micro found."}), 404
    return jsonify({"status": "success", "microcycle": user_microcycle.to_dict()}), 200


# Gives four mirocycles for mesocycle.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def microcycle_initializer():

    user_mesocycle = current_mesocycle(current_user.id)

    print(user_mesocycle.duration)

    # Each microcycle must last 1 week.
    microcycle_duration = timedelta(weeks=1)

    # Find how many one week microcycles will be present in the mesocycle
    microcycle_count = user_mesocycle.duration.days // microcycle_duration.days

    microcycle_start = user_mesocycle.start_date

    microcycles = []

    # Create a 
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
    return result

