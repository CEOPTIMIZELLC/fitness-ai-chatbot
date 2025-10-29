from flask import request, jsonify
from flask_login import current_user, login_required

from app.main_sub_agents.user_equipment import create_equipment_agent as create_agent
from app.models import Equipment_Library

from app.database_to_frontend.user_equipment import ItemRetriever

from .blueprint_factories.subagent_items import create_subagent_crud_blueprint

# ----------------------------------------- User Equipment -----------------------------------------

item_name = "user_equipment"
focus_name = "equipment"

bp = create_subagent_crud_blueprint(
    name = item_name, 
    url_prefix = "/" + item_name, 
    item_class = ItemRetriever
)

# Constructs the message relating to the piece of equipment.
def item_request_constructor(i_id, i_name, i_measurement):
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

# Constructs a request message for the agent based on endpoint inputs.
def example_request_creator(data, alter_old):
    equipment_id = data.get("equipment_id")
    equipment_name = data.get("equipment_name")
    equipment_measurement = data.get("measurement")
    equipment_request_message = item_request_constructor(equipment_id, equipment_name, equipment_measurement)

    if alter_old:
        user_equipment_id = data.get("user_equipment_id")
        if user_equipment_id:
            equipment_request_message = f"equipment of id {user_equipment_id}"
            
        new_equipment_id = data.get("new_equipment_id")
        new_equipment_name = data.get("new_equipment_name")
        new_equipment_measurement = data.get("new_measurement")
        new_equipment_request_message = item_request_constructor(new_equipment_id, new_equipment_name, new_equipment_measurement)

        return f"I would like to change my {equipment_request_message} to a {new_equipment_request_message}."

    return f"I would like to add a {equipment_request_message}."

# Retrieve current user's equipment
@bp.route('/sub_agent_test', methods=['GET'])
@login_required
def get_user_equipment_list():
    # Input is a json.
    if not request.is_json:
        data={}
    else:
        data = request.get_json()

    state = {
        "user_id": current_user.id,
        "equipment_is_requested": True,
        "equipment_is_alter": False,
        "equipment_is_read": True,
        "equipment_read_plural": True,
        "equipment_read_current": True,
        "equipment_detail": "Retrieve current equipment.",
        "equipment_alter_old": None, 

        "item_id": data.get("user_equipment_id"), 
        "equipment_id": data.get("equipment_id"), 
        "equipment_measurement": data.get("measurement"), 
    }
    equipment_agent = create_agent()

    result = equipment_agent.invoke(state)
    return jsonify({"status": "success", "response": result}), 200


# Retrieve current user's equipment
@bp.route('/sub_agent_test/<user_equipment_id>', methods=['GET'])
@login_required
def read_user_equipment(user_equipment_id):
    state = {
        "user_id": current_user.id,
        "equipment_is_requested": True,
        "equipment_is_alter": False,
        "equipment_is_read": True,
        "equipment_read_plural": True,
        "equipment_read_current": True,
        "equipment_detail": "Retrieve current equipment.",
        "equipment_alter_old": None, 

        "item_id": user_equipment_id, 
    }
    equipment_agent = create_agent()

    result = equipment_agent.invoke(state)
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

    request_message = example_request_creator(data, alter_old=False)

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

    request_message = example_request_creator(data, alter_old=True)

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

    request_message = example_request_creator(data, alter_old=True)

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
    return jsonify({"status": "success", "response": result}), 200