from flask import Blueprint, jsonify
from app.utils.db_helpers import get_all_items, get_item_by_id

def create_library_crud_blueprint(name, url_prefix, model, response_key):
    bp = Blueprint(name, __name__, url_prefix=url_prefix)

    @bp.route('/', methods=['GET'])
    def list_items():
        result = get_all_items(model)
        return jsonify({"status": "success", response_key: result}), 200

    @bp.route('/<item_id>', methods=['GET'])
    def read_item(item_id):
        result = get_item_by_id(model, item_id)
        if not result:
            return jsonify({
                "status": "error",
                "message": f"{response_key[:-1].capitalize()} {item_id} not found."
            }), 404
        return jsonify({"status": "success", response_key: result}), 200

    return bp
