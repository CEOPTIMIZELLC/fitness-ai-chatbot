from app.models import User_Training_Constraints, User_Training_Available_Equipment, User_Training_Equipment_Measurements

user_training_constraints = [
    User_Training_Constraints(user_id=1, max_session_time_minutes=60, days_per_week=7)
]

user_training_available_equipment = [
    User_Training_Available_Equipment(user_training_constraints_id=1, equipment_id=1),
    User_Training_Available_Equipment(user_training_constraints_id=1, equipment_id=2)
]

user_training_equipment_measurements = [
    User_Training_Equipment_Measurements(user_equipment_id=1, measurement_id=1, measurement=12),
    User_Training_Equipment_Measurements(user_equipment_id=1, measurement_id=2, measurement=10),
    User_Training_Equipment_Measurements(user_equipment_id=2, measurement_id=2, measurement=30)
]