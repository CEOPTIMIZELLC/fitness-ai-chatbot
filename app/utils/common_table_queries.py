from datetime import date
from app.models import Goal_Library, User_Macrocycles, User_Mesocycles, User_Microcycles, User_Workout_Days

# Retrieve the latest, currently active macrocycle for a user.
def current_macrocycle(user_id):
    today = date.today()
    active_macrocycle = (
        User_Macrocycles.query
        .filter(
            User_Macrocycles.user_id == user_id,
            User_Macrocycles.start_date <= today, 
            User_Macrocycles.end_date >= today)
        .order_by(User_Macrocycles.id.desc())
        .first())
    return active_macrocycle

# Retrieve the latest, currently active mesocycle for a user.
def current_mesocycle(user_id):
    today = date.today()
    active_mesocycle = (
        User_Mesocycles.query
        .join(User_Macrocycles)
        .filter(
            User_Macrocycles.user_id == user_id,
            User_Mesocycles.start_date <= today, 
            User_Mesocycles.end_date >= today)
        .order_by(User_Mesocycles.id.desc())
        .first())
    return active_mesocycle

# Retrieve the latest, currently active microcycle for a user.
def current_microcycle(user_id):
    today = date.today()
    active_microcycle = (
        User_Microcycles.query
        .join(User_Mesocycles)
        .join(User_Macrocycles)
        .filter(
            User_Macrocycles.user_id == user_id,
            User_Microcycles.start_date <= today, 
            User_Microcycles.end_date >= today)
        .order_by(User_Microcycles.id.desc())
        .first())
    return active_microcycle

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

