from app import db
from app.models import Weekday_Library

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