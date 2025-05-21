from flask import jsonify, Blueprint
from app.models import Phase_Component_Library
from app.utils.db_helpers import get_all_items, get_item_by_id

bp = Blueprint('phase_components', __name__)

# ----------------------------------------- Phase Components -----------------------------------------

# Retrieve phase components
@bp.route('/', methods=['GET'])
def get_phase_components_list():
    result = get_all_items(Phase_Component_Library)
    return jsonify({"status": "success", "phase_components": result}), 200

# Show phase components based on id.
@bp.route('/<phase_component_id>', methods=['GET'])
def read_phase_component(phase_component_id):
    result = get_item_by_id(Phase_Component_Library, phase_component_id)
    if not result:
        return jsonify({
            "status": "error", 
            "message": f"Phase Component {phase_component_id} not found."
        }), 404
    return jsonify({"status": "success", "phase_components": result}), 200
