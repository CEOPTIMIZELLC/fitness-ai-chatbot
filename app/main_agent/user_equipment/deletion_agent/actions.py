from app.db_session import session_scope
from app.models import User_Equipment

from ..actions import filter_items_by_query, construct_query_filters

# Delete an old piece of equipment for the user.
def delete_singular(state):
    # Construct the queries.
    query_filters = construct_query_filters(
        user_id = state["user_id"], 
        item_id = state.get("item_id", None), 
        equipment_id = state.get("equipment_id", None), 
        measurement = state.get("equipment_measurement", None)
    )

    with session_scope() as s:
        filtered_equipment = s.query(User_Equipment).filter(*query_filters).all()
        item_count = len(filtered_equipment)

        # Perform deletion on the only item found.
        if item_count == 1:
            schedule_dict = filtered_equipment[0].to_dict()

            # Delete the requested item.
            requested_item_id = filtered_equipment[0].id
            s.query(User_Equipment).filter_by(id=requested_item_id).delete()

            return [schedule_dict]

        schedule_dict = [
            item.to_dict()
            for item in filtered_equipment
        ]

    return schedule_dict



