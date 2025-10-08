from datetime import date

from app.models import User_Macrocycles

# Retrieve the latest, currently active macrocycle for a user.
def currently_active_item(user_id):
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