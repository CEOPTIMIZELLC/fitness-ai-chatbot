from flask import request, jsonify
from flask_login import current_user, login_required

from app.main_sub_agents.user_equipment import create_equipment_agent as create_agent
from app.models import Equipment_Library

from app.database_to_frontend.user_equipment import ItemRetriever

from .blueprint_factories.subagent_items import create_item_blueprint

# ----------------------------------------- User Equipment -----------------------------------------

item_name = "user_equipment"
focus_name = "equipment"

bp = create_item_blueprint(
    item_name, focus_name, 
    item_retriever = ItemRetriever, 
    current_retriever = None, 
    create_agent = create_agent, 
    add_test_retrievers = False, 
    add_initializers = False
)

# Constructs the message relating to the piece of equipment.
def item_request_constructor(unique_id=None, i_id=None, i_name=None, i_measurement=None):
    if unique_id:
        return f"equipment of id {unique_id}"

    item_request_message = "piece of equipment"

    # Get the name of the equipment for the request.
    if (not i_name) and i_id:
        item = Equipment_Library.query.filter_by(id=i_id).first()
        i_name = item.name
    
    if not (i_name or i_measurement):
        return item_request_message
    
    if i_name:
        item_request_message = f"{i_name} equipment"
    
    if i_measurement:
        item_request_message += f" measuring {i_measurement}"
    return item_request_message

def get_request(data):
    equipment_request_message = item_request_constructor(
        unique_id = data.get("user_equipment_id"), 
        i_id = data.get("equipment_id"), 
        i_name = data.get("equipment_name"), 
        i_measurement = data.get("measurement"), 
    )

    request_message = f"I would like to look at my {equipment_request_message}."

    state = {
        "user_id": current_user.id,
        "equipment_is_requested": True,
        "equipment_is_alter": False,
        "equipment_is_read": True,
        "equipment_read_plural": True,
        "equipment_read_current": True,
        "equipment_detail": request_message,
        "equipment_alter_old": None, 
    }
    equipment_agent = create_agent()

    result = equipment_agent.invoke(state)
    return result

def creation_request(data):
    equipment_request_message = item_request_constructor(
        i_id = data.get("equipment_id"), 
        i_name = data.get("equipment_name"), 
        i_measurement = data.get("measurement"), 
    )

    request_message = f"I would like to add a {equipment_request_message}."

    state = {
        "user_id": current_user.id,
        "equipment_is_requested": True,
        "equipment_is_alter": True,
        "equipment_is_read": True,
        "equipment_read_plural": False,
        "equipment_read_current": False,
        "equipment_detail": request_message,
        "equipment_alter_old": False, 
    }
    equipment_agent = create_agent()

    result = equipment_agent.invoke(state)
    return result

def alter_request(data):
    equipment_request_message = item_request_constructor(
        i_id = data.get("equipment_id"), 
        i_name = data.get("equipment_name"), 
        i_measurement = data.get("measurement"), 
        unique_id = data.get("user_equipment_id")
    )

    new_equipment_request_message = item_request_constructor(
        i_id = data.get("new_equipment_id"), 
        i_name = data.get("new_equipment_name"), 
        i_measurement = data.get("new_measurement")
    )

    request_message = f"I would like to change my {equipment_request_message} to a {new_equipment_request_message}."

    state = {
        "user_id": current_user.id,
        "equipment_is_requested": True,
        "equipment_is_alter": True,
        "equipment_is_read": True,
        "equipment_read_plural": False,
        "equipment_read_current": False,
        "equipment_detail": request_message,
        "equipment_alter_old": True, 
    }
    equipment_agent = create_agent()

    result = equipment_agent.invoke(state)
    return result

# Retrieve current user's equipment
@bp.route('/sub_agent_test', methods=['GET'])
@login_required
def get_user_equipment_list():
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()

    result = get_request(data)
    return jsonify({"status": "success", "response": result}), 200


# Retrieve current user's equipment
@bp.route('/sub_agent_test/<user_equipment_id>', methods=['GET'])
@login_required
def read_user_equipment(user_equipment_id):
    data = {
        "user_equipment_id": user_equipment_id
    }

    result = get_request(data)
    return jsonify({"status": "success", "response": result}), 200

# Add current user's equipment
@bp.route('/', methods=['POST'])
@login_required
def add_user_equipment():
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()

    result = creation_request(data)
    return jsonify({"status": "success", "response": result}), 200

# Change current user's equipment
@bp.route('/', methods=['PATCH'])
@login_required
def change_user_equipment():
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()

    result = alter_request(data)
    return jsonify({"status": "success", "response": result}), 200

# Change current user's equipment
@bp.route('/<user_equipment_id>', methods=['PATCH'])
@login_required
def change_user_equipment_by_id(user_equipment_id):
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()
    data["user_equipment_id"] = user_equipment_id

    result = alter_request(data)
    return jsonify({"status": "success", "response": result}), 200