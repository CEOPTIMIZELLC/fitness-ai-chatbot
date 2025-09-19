from app.db_session import session_scope
from app.models import User_Equipment

from ..actions import filter_items_by_query, construct_query_filters

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



