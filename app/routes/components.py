from flask import jsonify, Blueprint
from app.models import Component_Library
from app.utils.db_helpers import get_all_items, get_item_by_id

bp = Blueprint('components', __name__)

@bp.route('/', methods=['GET'])
def get_components_list():
    result = get_all_items(Component_Library)
    return jsonify({"status": "success", "components": result}), 200

@bp.route('/<component_id>', methods=['GET'])
def read_component(component_id):
    result = get_item_by_id(Component_Library, component_id)
    if not result:
        return jsonify({
            "status": "error", 
            "message": f"Component {component_id} not found."
        }), 404
    return jsonify({"status": "success", "components": result}), 200