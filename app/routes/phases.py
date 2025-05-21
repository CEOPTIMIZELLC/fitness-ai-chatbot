from flask import jsonify, Blueprint
from app.models import Phase_Library
from app.utils.db_helpers import get_all_items, get_item_by_id

bp = Blueprint('phases', __name__)

# ----------------------------------------- Phases -----------------------------------------

# Retrieve phases
@bp.route('/', methods=['GET'])
def get_phase_list():
    result = get_all_items(Phase_Library)
    return jsonify({"status": "success", "phases": result}), 200

# Show phases based on id.
@bp.route('/<phase_id>', methods=['GET'])
def read_phase(phase_id):
    result = get_item_by_id(Phase_Library, phase_id)
    if not result:
        return jsonify({
            "status": "error", 
            "message": f"Phase {phase_id} not found."
        }), 404
    return jsonify({"status": "success", "phases": result}), 200
