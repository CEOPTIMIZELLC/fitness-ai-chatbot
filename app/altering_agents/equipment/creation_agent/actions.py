from app.db_session import session_scope
from app.models import User_Equipment

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