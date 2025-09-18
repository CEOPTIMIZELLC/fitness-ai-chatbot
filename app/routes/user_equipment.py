from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_required

from app import db
from app.models import User_Equipment

from app.main_agent.user_equipment import create_equipment_agent

bp = Blueprint('user_equipment', __name__)

# ----------------------------------------- User Equipment -----------------------------------------

# Retrieve current user's equipment
@bp.route('/', methods=['GET'])
@login_required
def get_user_equipment_list():
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()

    state = {
        "user_id": current_user.id,
        "equipment_impacted": True,
        "equipment_is_altered": False,
        "equipment_read_plural": True,
        "equipment_read_current": True,
        "equipment_message": "Retrieve current equipment.",
        "equipment_alter_old": None, 

        "item_id": data.get("item_id"), 
        "equipment_id": data.get("equipment_id"), 
        "equipment_measurement": data.get("measurement"), 
    }
    equipment_agent = create_equipment_agent()

    result = equipment_agent.invoke(state)
    return jsonify({"status": "success", "user_equipment": result}), 200


# Retrieve current user's equipment
@bp.route('/<user_equipment_id>', methods=['GET'])
@login_required
def read_user_equipment(user_equipment_id):
    user_equipment = db.session.get(User_Equipment, user_equipment_id)
    if not user_equipment:
        abort(404, description=f"No active equipment of {user_equipment_id} found for current user.")
    return jsonify({"status": "success", "user_equipment": user_equipment.to_dict()}), 200

# Add current user's equipment
@bp.route('/<equipment_id>', methods=['POST'])
@login_required
def add_user_equipment(equipment_id):
    # Input is a json.
    data = request.get_json()
    if not data:
        abort(404, description="Invalid request")
    
    if ('measurement' not in data):
        abort(400, description="Please fill out the form!")

    user_equipment = User_Equipment(user_id=current_user.id, equipment_id=equipment_id, measurement=data["measurement"])
    db.session.add(user_equipment)
    db.session.commit()
    return jsonify({"status": "success", "user_equipment": user_equipment.to_dict()}), 200

# Retrieve current user's equipment of a specific type
@bp.route('/equipment/<equipment_id>', methods=['GET'])
@login_required
def read_user_equipment_by_type(equipment_id):
    user_equipment = User_Equipment.query.filter_by(user_id=current_user.id, equipment_id=equipment_id).all()
    if not user_equipment:
        abort(404, description=f"No active equipment of {equipment_id} found for current user.")
    result = []
    for equipment in user_equipment:
        result.append(equipment.to_dict())
    return jsonify({"status": "success", "user_equipment": result}), 200