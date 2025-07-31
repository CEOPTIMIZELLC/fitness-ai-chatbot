from datetime import date
from app.models import User_Macrocycles, User_Mesocycles

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