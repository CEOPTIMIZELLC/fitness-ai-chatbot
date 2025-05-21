from flask import jsonify, Blueprint

from app.models import Equipment_Library
from app.utils.db_helpers import get_all_items, get_item_by_id

bp = Blueprint('equipment', __name__)

# ----------------------------------------- Equipment -----------------------------------------

# Retrieve equipment
@bp.route('/', methods=['GET'])
def get_equipment_list():
    result = get_all_items(Equipment_Library)
    return jsonify({"status": "success", "equipment": result}), 200

# Show equipment based on id.
@bp.route('/<equipment_id>', methods=['GET'])
def read_equipment(equipment_id):
    result = get_item_by_id(Equipment_Library, equipment_id)
    if not result:
        return jsonify({
            "status": "error", 
            "message": f"Equipment {equipment_id} not found."
        }), 404
    return jsonify({"status": "success", "equipment": result}), 200
