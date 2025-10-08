from datetime import date

from app.models import User_Weekday_Availability

# Retrieve the latest, currently active workday for a user.
def currently_active_item(user_id):
    # Get the weekday as an integer (0 for Monday, 6 for Sunday)
    today = date.today().weekday()
    active_weekday_availability = (
        User_Weekday_Availability.query
        .filter(
            User_Weekday_Availability.user_id == user_id,
            User_Weekday_Availability.weekday_id == today)
        .first())
    return active_weekday_availability