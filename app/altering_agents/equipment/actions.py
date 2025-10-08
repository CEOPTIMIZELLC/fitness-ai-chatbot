from logging_config import LogAlteringAgent

from app.db_session import session_scope
from app.models import Equipment_Library, User_Equipment


def construct_query_filters(user_id, item_id=None, equipment_id=None, measurement=None):
    query_filters = [User_Equipment.user_id == user_id]

    LogAlteringAgent.agent_steps(f"\tFiltering by:")

    # If the direct id has been provided, no more filters are needed.
    if item_id:
        LogAlteringAgent.agent_steps(f"\t\tID = {item_id}")
        query_filters.append(User_Equipment.id == item_id)
        return query_filters
    
    if equipment_id:
        LogAlteringAgent.agent_steps(f"\t\tEquipment ID = {equipment_id}")
        query_filters.append(User_Equipment.equipment_id == equipment_id)
    if measurement:
        LogAlteringAgent.agent_steps(f"\t\tMeasurement = {measurement}")
        query_filters.append(User_Equipment.measurement == measurement)
    
    if not (item_id or equipment_id or measurement):
        LogAlteringAgent.agent_steps(f"\t\tAll.")
    return query_filters

# Filter the list of user equipment based on user filters.
def filter_items_by_query(state):
    # Construct the queries.
    query_filters = construct_query_filters(
        user_id = state["user_id"], 
        item_id = state.get("item_id", None), 
        equipment_id = state.get("equipment_id", None), 
        measurement = state.get("equipment_measurement", None)
    )

    with session_scope() as s:
        filtered_equipment = s.query(User_Equipment).filter(*query_filters).all()

        filtered_equipment_dicts = [
            item.to_dict()
            for item in filtered_equipment
        ]

    return filtered_equipment_dicts

# Extract the goal class items from the goal class.
def extract_sub_goal_class_info(new_details, goal_class, key_name="equipment"):
    equipment_id = goal_class.equipment_id
    equipment_measurement = goal_class.equipment_measurement

    if equipment_id:
        item = Equipment_Library.query.filter_by(id=equipment_id).first()
        new_details[f"{key_name}_id"] = equipment_id
        new_details[f"{key_name}_name"] = item.name
    if equipment_measurement:
        new_details[f"{key_name}_measurement"] = equipment_measurement

    return new_details

# Alter an old piece of equipment for the user.
def alter_singular(state):
    # Construct the queries.
    query_filters = construct_query_filters(
        user_id = state["user_id"], 
        item_id = state.get("item_id", None), 
        equipment_id = state.get("equipment_id", None), 
        measurement = state.get("equipment_measurement", None)
    )

    new_equipment_id = state.get("new_equipment_id", None)
    new_measurement = state.get("new_equipment_measurement", None)

    with session_scope() as s:
        filtered_equipment = s.query(User_Equipment).filter(*query_filters).all()
        item_count = len(filtered_equipment)

        # Perform edit on the only item found.
        if item_count == 1:
            requested_item = filtered_equipment[0]
            if new_equipment_id:
                requested_item.equipment_id = new_equipment_id
            if new_measurement:
                requested_item.measurement = new_measurement

        schedule_dict = [
            item.to_dict()
            for item in filtered_equipment
        ]

    return schedule_dict
