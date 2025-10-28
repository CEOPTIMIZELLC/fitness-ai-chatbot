from flask import Blueprint, jsonify
from app.utils.db_helpers import get_all_items, get_item_by_id

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




from flask_login import current_user
from app.utils.item_to_string import recursively_change_dict_timedeltas

def agent_invoker(agent_creation_caller, state):
    subagent = agent_creation_caller()

    result = subagent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"status": "success", "response": result}), 200

# Retrieve current user's list of items.
def get_user_list(focus_name, agent_creation_caller):
    state = {
        "user_id": current_user.id,
        f"{focus_name}_is_requested": True,
        f"{focus_name}_is_alter": False,
        f"{focus_name}_is_read": True,
        f"{focus_name}_read_plural": True,
        f"{focus_name}_read_current": False,
        f"{focus_name}_detail": f"Retrieve all of my {focus_name}s."
    }
    return agent_invoker(agent_creation_caller, state)

# Retrieve user's list of items for the current parent.
def get_user_current_list(focus_name, agent_creation_caller):
    state = {
        "user_id": current_user.id,
        f"{focus_name}_is_requested": True,
        f"{focus_name}_is_alter": False,
        f"{focus_name}_is_read": True,
        f"{focus_name}_read_plural": True,
        f"{focus_name}_read_current": True,
        f"{focus_name}_detail": f"Retrieve all current {focus_name}."
    }
    return agent_invoker(agent_creation_caller, state)

# Retrieve user's current item.
def read_user_current(focus_name, agent_creation_caller):
    state = {
        "user_id": current_user.id,
        f"{focus_name}_is_requested": True,
        f"{focus_name}_is_alter": False,
        f"{focus_name}_is_read": True,
        f"{focus_name}_read_plural": False,
        f"{focus_name}_read_current": True,
        f"{focus_name}_detail": f"Retrieve my current {focus_name}."
    }
    return agent_invoker(agent_creation_caller, state)

# Initialize user's list of items for the current parent.
def item_initializer(focus_name, agent_creation_caller, user_message=None):
    if not user_message:
        user_message = f"Perform {focus_name} scheduling."
    state = {
        "user_id": current_user.id,
        f"{focus_name}_is_requested": True,
        f"{focus_name}_is_alter": True,
        f"{focus_name}_is_read": True,
        f"{focus_name}_read_plural": False,
        f"{focus_name}_read_current": False,
        f"{focus_name}_detail": user_message
    }
    return agent_invoker(agent_creation_caller, state)


# Initialize user's list of items for the current parent.
def item_initializer_with_parent_id(focus_name, agent_creation_caller, parent_id, user_message=None):
    if not user_message:
        user_message = f"Perform {focus_name} scheduling."
    state = {
        "user_id": current_user.id,
        f"{focus_name}_is_requested": True,
        f"{focus_name}_is_alter": True,
        f"{focus_name}_is_read": True,
        f"{focus_name}_read_plural": False,
        f"{focus_name}_read_current": False,
        f"{focus_name}_perform_with_parent_id": parent_id, 
        f"{focus_name}_detail": user_message
    }
    return agent_invoker(agent_creation_caller, state)



