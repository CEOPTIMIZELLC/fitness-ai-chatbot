from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_required

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
    state = {
        "user_id": current_user.id,
        "equipment_impacted": True,
        "equipment_is_altered": False,
        "equipment_read_plural": True,
        "equipment_read_current": True,
        "equipment_message": "Retrieve current equipment.",
        "equipment_alter_old": None, 

        "item_id": user_equipment_id, 
    }
    equipment_agent = create_equipment_agent()

    result = equipment_agent.invoke(state)
    return jsonify({"status": "success", "user_equipment": result}), 200

# Add current user's equipment
@bp.route('/', methods=['POST'])
@login_required
def add_user_equipment():
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()

    state = {
        "user_id": current_user.id,
        "equipment_impacted": True,
        "equipment_is_altered": True,
        "equipment_read_plural": False,
        "equipment_read_current": False,
        "equipment_message": "Add new equipment.",
        "equipment_alter_old": False, 

        "equipment_id": data.get("equipment_id"), 
        "equipment_measurement": data.get("measurement"), 
    }
    equipment_agent = create_equipment_agent()

    result = equipment_agent.invoke(state)
    return jsonify({"status": "success", "user_equipment": result}), 200


# Change current user's equipment
@bp.route('/', methods=['PATCH'])
@login_required
def change_user_equipment():
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()

    state = {
        "user_id": current_user.id,
        "equipment_impacted": True,
        "equipment_is_altered": True,
        "equipment_read_plural": False,
        "equipment_read_current": False,
        "equipment_message": "Change old equipment.",
        "equipment_alter_old": True, 

        "item_id": data.get("item_id"), 
        "equipment_id": data.get("equipment_id"), 
        "equipment_measurement": data.get("measurement"), 
    }
    equipment_agent = create_equipment_agent()

    result = equipment_agent.invoke(state)
    return jsonify({"status": "success", "user_equipment": result}), 200

# Change current user's equipment
@bp.route('/<user_equipment_id>', methods=['PATCH'])
@login_required
def change_user_equipment_by_id(user_equipment_id):
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()

    state = {
        "user_id": current_user.id,
        "equipment_impacted": True,
        "equipment_is_altered": True,
        "equipment_read_plural": False,
        "equipment_read_current": False,
        "equipment_message": "Change old equipment.",
        "equipment_alter_old": True, 

        "item_id": user_equipment_id, 
        "equipment_id": data.get("equipment_id"), 
        "equipment_measurement": data.get("measurement"), 
    }
    equipment_agent = create_equipment_agent()

    result = equipment_agent.invoke(state)
    return jsonify({"status": "success", "user_equipment": result}), 200