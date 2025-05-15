from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import User_Equipment

bp = Blueprint('user_equipment', __name__)

# ----------------------------------------- User Equipment -----------------------------------------

# Retrieve current user's equipment
@bp.route('/', methods=['GET'])
@login_required
def get_user_equipment_list():
    user_equipment = current_user.equipment
    result = []
    for equipment in user_equipment:
        result.append(equipment.to_dict())
    return jsonify({"status": "success", "user_equipment": result}), 200


# Retrieve current user's equipment
@bp.route('/<user_equipment_id>', methods=['GET'])
@login_required
def read_user_equipment(user_equipment_id):
    user_equipment = db.session.get(User_Equipment, user_equipment_id)
    if not user_equipment:
        return jsonify({"status": "error", "message": f"No active equipment of {user_equipment_id} found for current user."}), 404
    return jsonify({"status": "success", "user_equipment": user_equipment.to_dict()}), 200

# Add current user's equipment
@bp.route('/<equipment_id>', methods=['POST'])
@login_required
def add_user_equipment(equipment_id):
    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    
    if ('measurement' not in data):
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400

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
        return jsonify({"status": "error", "message": f"No active equipment of {equipment_id} found for current user."}), 404
    result = []
    for equipment in user_equipment:
        result.append(equipment.to_dict())
    return jsonify({"status": "success", "user_equipment": result}), 200