from datetime import date
from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles, User_Workout_Days

# Retrieve the latest, currently active workday for a user.
def current_workout_day(user_id):
    today = date.today()
    active_workout_day = (
        User_Workout_Days.query
        .join(User_Microcycles)
        .join(User_Mesocycles)
        .join(User_Macrocycles)
        .filter(
            User_Macrocycles.user_id == user_id,
            User_Workout_Days.date == today)
        .order_by(User_Workout_Days.id.desc())
        .first())
    return active_workout_day