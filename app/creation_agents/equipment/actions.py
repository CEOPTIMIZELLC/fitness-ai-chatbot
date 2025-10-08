from logging_config import LogCreationAgent

from app.db_session import session_scope
from app.models import User_Equipment


def construct_query_filters(user_id, item_id=None, equipment_id=None, measurement=None):
    query_filters = [User_Equipment.user_id == user_id]

    LogCreationAgent.agent_steps(f"\tFiltering by:")

    # If the direct id has been provided, no more filters are needed.
    if item_id:
        LogCreationAgent.agent_steps(f"\t\tID = {item_id}")
        query_filters.append(User_Equipment.id == item_id)
        return query_filters
    
    if equipment_id:
        LogCreationAgent.agent_steps(f"\t\tEquipment ID = {equipment_id}")
        query_filters.append(User_Equipment.equipment_id == equipment_id)
    if measurement:
        LogCreationAgent.agent_steps(f"\t\tMeasurement = {measurement}")
        query_filters.append(User_Equipment.measurement == measurement)
    
    if not (item_id or equipment_id or measurement):
        LogCreationAgent.agent_steps(f"\t\tAll.")
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

# Create a new piece of equipment for the user.
def create_singular(state):
    equipment_id = state.get("equipment_id")
    equipment_measurement = state.get("equipment_measurement")

    # Requires equipment id AND equipment measurement to create a new entry.
    if not(equipment_id and equipment_measurement):
        return None
    
    user_id = state["user_id"]
    payload = {}
    with session_scope() as s:
        user_equipment = User_Equipment(user_id=user_id, equipment_id=equipment_id, measurement=equipment_measurement)
        s.add(user_equipment)

        # get PKs without committing the transaction
        s.flush()

        # load defaults/server-side values
        s.refresh(user_equipment)
        payload = user_equipment.to_dict()

    return payload