from app.models import User_Equipment
def get_default_user_equipment():
    return [
        User_Equipment(user_id=1, equipment_id=1, measurement=10),
        User_Equipment(user_id=1, equipment_id=3, measurement=33),
        User_Equipment(user_id=1, equipment_id=3, measurement=32),
        User_Equipment(user_id=1, equipment_id=3, measurement=33),
        User_Equipment(user_id=1, equipment_id=4, measurement=45),
        User_Equipment(user_id=1, equipment_id=3, measurement=33),
        User_Equipment(user_id=1, equipment_id=8, measurement=20),
        User_Equipment(user_id=1, equipment_id=17, measurement=170),
        User_Equipment(user_id=1, equipment_id=17, measurement=175)
    ]
