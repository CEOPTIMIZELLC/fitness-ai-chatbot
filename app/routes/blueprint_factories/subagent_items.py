from logging_config import LogRoute

import inspect

from flask import request, jsonify, Blueprint, abort
from flask_login import login_required, current_user

from app.utils.item_to_string import recursively_change_dict_timedeltas

# Retrieves the user input, if there is one.
def _input_retriever(focus_name, request):
    # Input is a json.
    if request.is_json:
        data = request.get_json()
        return data.get(focus_name, f"Perform {focus_name} scheduling.")
    return f"Perform {focus_name} scheduling."

# Repeated method that invokes the agent.
def _agent_invoker(agent_creation_caller, state):
    subagent = agent_creation_caller()

    result = subagent.invoke(state)

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)

    return jsonify({"status": "success", "response": result}), 200

# Repeated method that invokes the agent.
def _state_name_retriever(focus_name):
    return {
        "is_requested": f"{focus_name}_is_requested",
        "is_alter": f"{focus_name}_is_alter",
        "is_read": f"{focus_name}_is_read",
        "read_plural": f"{focus_name}_read_plural",
        "read_current": f"{focus_name}_read_current",
        "perform_with_parent_id": f"{focus_name}_perform_with_parent_id",
        "detail": f"{focus_name}_detail",
        "detail_read_list": f"Retrieve all of my {focus_name}s.",
        "detail_read_current_list": f"Retrieve all current {focus_name}.",
        "detail_read_current": f"Retrieve my current {focus_name}.",
        "detail_initializer": f"Perform {focus_name} scheduling.",
    }

# Creates the initial blueprint for routes relating to the retrieval of subagent items from the database.
def create_subagent_crud_blueprint(name, url_prefix, item_class):
    bp = Blueprint(name, __name__, url_prefix=url_prefix)

    # Retrieve current user's list of items.
    @bp.route('/', methods=['GET'])
    @login_required
    def get_user_list():
        return item_class.list_items(current_user.id)

    # Retrieve current user's list of items.
    @bp.route('/<item_id>', methods=['GET'])
    @login_required
    def read_user_item(item_id):
        return item_class.get_item(current_user.id, item_id)

    # Retrieve current user's list of items.
    @bp.route('/filter', methods=['GET'])
    @login_required
    def filter_user_list():
        # Input is a json.
        if request.is_json:
            data = request.get_json()
        else:
            data = {}

        return item_class.filter_items(current_user.id, data)

    return bp

# Adds the routes to retrieve the currently active element(s).
def add_current_retrievers_to_subagent_crud_blueprint(bp, item_class):
    # Retrieve user's list of items for the current parent.
    @bp.route('/current_list', methods=['GET'])
    @login_required
    def get_user_current_list():
        return item_class.list_items_from_current_parent(current_user.id)

    # Retrieve user's current item.
    @bp.route('/current', methods=['GET'])
    @login_required
    def read_user_current():
        return item_class.read_current_item(current_user.id)

    return bp

# Adds the subagent calls that will read the items.
def add_test_retrievers_to_subagent_crud_blueprint(bp, state_names, agent_creation_caller):
    # Retrieve current user's list of items.
    @bp.route('/sub_agent_test', methods=['GET'])
    @login_required
    def get_user_list_sub_agent_call():
        state = {
            "user_id": current_user.id,
            state_names["is_requested"]: True,
            state_names["is_alter"]: False,
            state_names["is_read"]: True,
            state_names["read_plural"]: True,
            state_names["read_current"]: False,
            state_names["detail"]: state_names["detail_read_list"]
        }
        return _agent_invoker(agent_creation_caller, state)

    # Retrieve user's list of items for the current parent.
    @bp.route('/sub_agent_test/current_list', methods=['GET'])
    @login_required
    def get_user_current_list_sub_agent_call():
        state = {
            "user_id": current_user.id,
            state_names["is_requested"]: True,
            state_names["is_alter"]: False,
            state_names["is_read"]: True,
            state_names["read_plural"]: True,
            state_names["read_current"]: True,
            state_names["detail"]: state_names["detail_read_current_list"]
        }
        return _agent_invoker(agent_creation_caller, state)

    # Retrieve user's current item.
    @bp.route('/sub_agent_test/current', methods=['GET'])
    @login_required
    def read_user_current_sub_agent_call():
        state = {
            "user_id": current_user.id,
            state_names["is_requested"]: True,
            state_names["is_alter"]: False,
            state_names["is_read"]: True,
            state_names["read_plural"]: False,
            state_names["read_current"]: True,
            state_names["detail"]: state_names["detail_read_current"]
        }
        return _agent_invoker(agent_creation_caller, state)
    
    return bp

# Adds the subagent calls that will initialize the items.
def add_initializer_to_subagent_crud_blueprint(bp, state_names, agent_creation_caller, request_name):
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
            state_names["detail"]: _input_retriever(request_name, request)
        }
        return _agent_invoker(agent_creation_caller, state)

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
            state_names["perform_with_parent_id"]: parent_id, 
            state_names["detail"]: _input_retriever(request_name, request)
        }
        return _agent_invoker(agent_creation_caller, state)

    return bp

def create_item_blueprint(item_name, focus_name, item_retriever, current_retriever, create_agent, add_test_retrievers=False, add_initializers=False, request_name=None):
    if not request_name:
        request_name = focus_name

    state_names = _state_name_retriever(focus_name)

    # Initial blueprint creation.
    LogRoute.bps(f"Subagent CRUD blueprint for {item_name}.")
    bp = create_subagent_crud_blueprint(
        name = item_name, 
        url_prefix = "/" + item_name, 
        item_class = item_retriever
    )

    # Add retrievers for current items.
    if inspect.isclass(current_retriever):
        LogRoute.bps(f"Added current item retrievers for {item_name}.")
        bp = add_current_retrievers_to_subagent_crud_blueprint(
            bp = bp, 
            item_class = current_retriever
        )

    # Add the endpoints for the sub agent retrievers.
    if add_test_retrievers and inspect.isfunction(create_agent):
        LogRoute.bps(f"Added sub agent driven retrievers for {item_name}.")
        bp = add_test_retrievers_to_subagent_crud_blueprint(
            bp = bp, 
            state_names = state_names, 
            agent_creation_caller = create_agent
        )
    
    # Add the endpoints for the sub agent schedule initializer.
    if add_initializers and inspect.isfunction(create_agent):
        LogRoute.bps(f"Added sub agent driven initialization for {item_name}.")
        bp = add_initializer_to_subagent_crud_blueprint(
            bp = bp, 
            state_names = state_names, 
            request_name = request_name, 
            agent_creation_caller = create_agent
        )
    
    return bp

