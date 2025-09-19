from logging_config import LogMainSubAgent

from app.db_session import session_scope
from app.models import User_Equipment


def construct_query_filters(user_id, item_id=None, equipment_id=None, measurement=None):
    query_filters = [User_Equipment.user_id == user_id]

    LogMainSubAgent.agent_steps(f"\tFiltering by:")

    # If the direct id has been provided, no more filters are needed.
    if item_id:
        LogMainSubAgent.agent_steps(f"\t\tID = {item_id}")
        query_filters.append(User_Equipment.id == item_id)
        return query_filters
    
    if equipment_id:
        LogMainSubAgent.agent_steps(f"\t\tEquipment ID = {equipment_id}")
        query_filters.append(User_Equipment.equipment_id == equipment_id)
    if measurement:
        LogMainSubAgent.agent_steps(f"\t\tMeasurement = {measurement}")
        query_filters.append(User_Equipment.measurement == measurement)
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