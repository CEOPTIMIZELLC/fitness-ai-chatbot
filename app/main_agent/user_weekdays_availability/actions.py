from flask_login import current_user

from app import db
from app.models import Weekday_Library, User_Weekday_Availability

from app.agents.weekday_availability import create_weekday_availability_extraction_graph

# ----------------------------------------- User Weekday Availability -----------------------------------------
# Retrieve possible weekday types.
def retrieve_weekday_types():
    weekdays = (
        db.session.query(
            Weekday_Library.id,
            Weekday_Library.name
        )
        .all()
    )

    return [
        {
            "id": weekday.id, 
            "name": weekday.name.lower()
        } 
        for weekday in weekdays
    ]