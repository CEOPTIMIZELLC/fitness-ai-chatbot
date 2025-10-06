from datetime import date

from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

# Retrieve the latest, currently active microcycle for a user.
def currently_active_item(user_id):
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