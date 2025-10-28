from flask import request, jsonify, Blueprint, abort
from flask_login import login_required, current_user

from app.utils.db_helpers import get_all_items, get_item_by_id
from app.utils.item_to_string import recursively_change_dict_timedeltas

def create_library_crud_blueprint(name, url_prefix, model, response_key):
    bp = Blueprint(name, __name__, url_prefix=url_prefix)

    @bp.route('/', methods=['GET'])
    def list_items():
        result = get_all_items(model)
        return jsonify({"status": "success", "response": result}), 200

    @bp.route('/print', methods=['GET'])
    def print_items():
        result_dict = get_all_items(model)
        result = [item["name"] for item in result_dict]
        print(result)
        return jsonify({"status": "success", "response": result}), 200

    @bp.route('/<item_id>', methods=['GET'])
    def read_item(item_id):
        result = get_item_by_id(model, item_id)
        if not result:
            return jsonify({"status": "error", "message": f"{response_key[:-1].capitalize()} {item_id} not found."}), 404
        return jsonify({"status": "success", "response": result}), 200

    return bp


def create_subagent_crud_blueprint(name, focus_name, url_prefix, agent_creation_caller):
    bp = Blueprint(name, __name__, url_prefix=url_prefix)

    state_names = {
        "is_requested": f"{focus_name}_is_requested",
        "is_alter": f"{focus_name}_is_alter",
        "is_read": f"{focus_name}_is_read",
        "read_plural": f"{focus_name}_read_plural",
        "read_current": f"{focus_name}_read_current",
        "detail": f"{focus_name}_detail",
        "detail_read_list": f"Retrieve all of my {focus_name}s.",
        "detail_read_current_list": f"Retrieve all current {focus_name}.",
        "detail_read_current": f"Retrieve my current {focus_name}.",
        "detail_initializer": f"Perform {focus_name} scheduling.",
    }

    # Retrieves the user input, if there is one.
    def input_retriever(request):
        # Input is a json.
        if request.is_json:
            data = request.get_json()
            return data.get(focus_name, f"Perform {focus_name} scheduling.")
        return f"Perform {focus_name} scheduling."

    def agent_invoker(state):
        subagent = agent_creation_caller()

        result = subagent.invoke(state)

        # Correct time delta for serializing for JSON output.
        result = recursively_change_dict_timedeltas(result)

        return jsonify({"status": "success", "response": result}), 200

    # Retrieve current user's list of items.
    @bp.route('/', methods=['GET'])
    @login_required
    def get_user_list():
        state = {
            "user_id": current_user.id,
            state_names["is_requested"]: True,
            state_names["is_alter"]: False,
            state_names["is_read"]: True,
            state_names["read_plural"]: True,
            state_names["read_current"]: False,
            state_names["detail"]: state_names["detail_read_list"]
        }
        return agent_invoker(state)

    # Retrieve user's list of items for the current parent.
    @bp.route('/current_list', methods=['GET'])
    @login_required
    def get_user_current_list():
        state = {
            "user_id": current_user.id,
            state_names["is_requested"]: True,
            state_names["is_alter"]: False,
            state_names["is_read"]: True,
            state_names["read_plural"]: True,
            state_names["read_current"]: True,
            state_names["detail"]: state_names["detail_read_current_list"]
        }
        return agent_invoker(state)

    # Retrieve user's current item.
    @bp.route('/current', methods=['GET'])
    @login_required
    def read_user_current():
        state = {
            "user_id": current_user.id,
            state_names["is_requested"]: True,
            state_names["is_alter"]: False,
            state_names["is_read"]: True,
            state_names["read_plural"]: False,
            state_names["read_current"]: True,
            state_names["detail"]: state_names["detail_read_current"]
        }
        return agent_invoker(state)

    # Initialize user's list of items for the current parent.
    @bp.route('/', methods=['POST', 'PATCH'])
    @login_required
    def item_initializer():
        state = {
            "user_id": current_user.id,
            state_names["is_requested"]: True,
            state_names["is_alter"]: True,
            state_names["is_read"]: True,
            state_names["read_plural"]: False,
            state_names["read_current"]: False,
            f"{focus_name}_detail": input_retriever(request)
        }
        return agent_invoker(state)

    # Initialize user's list of items for the current parent.
    @bp.route('/<parent_id>', methods=['POST', 'PATCH'])
    @login_required
    def item_initializer_with_parent_id(parent_id):
        state = {
            "user_id": current_user.id,
            state_names["is_requested"]: True,
            state_names["is_alter"]: True,
            state_names["is_read"]: True,
            state_names["read_plural"]: False,
            state_names["read_current"]: False,
            f"{focus_name}_perform_with_parent_id": parent_id, 
            f"{focus_name}_detail": input_retriever(request)
        }
        return agent_invoker(state)

    return bp


