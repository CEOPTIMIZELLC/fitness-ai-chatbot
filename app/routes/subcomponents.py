from flask import jsonify, Blueprint
from app.models import Subcomponent_Library
from app.utils.db_helpers import get_all_items, get_item_by_id

bp = Blueprint('subcomponents', __name__)

@bp.route('/', methods=['GET'])
def get_subcomponents_list():
    result = get_all_items(Subcomponent_Library)
    return jsonify({"status": "success", "subcomponents": result}), 200

@bp.route('/<subcomponent_id>', methods=['GET'])
def read_subcomponent(subcomponent_id):
    result = get_item_by_id(Subcomponent_Library, subcomponent_id)
    if not result:
        return jsonify({
            "status": "error", 
            "message": f"Subcomponent {subcomponent_id} not found."
        }), 404
    return jsonify({"status": "success", "subcomponents": result}), 200