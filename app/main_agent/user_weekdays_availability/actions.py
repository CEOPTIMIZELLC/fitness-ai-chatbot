from logging_config import LogMainSubAgent

from datetime import timedelta
from calendar import day_name

from app import db
from app.db_session import session_scope
from app.models import Weekday_Library, User_Weekday_Availability, User_Workout_Days

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

# Initializes all of the weekdays that don't currently have an availability for the user.
def initialize_user_availability(s, user_id):
    LogMainSubAgent.agent_steps(f"\t---------Initialize all days.---------")

    # Update each availability entry to the database.
    for i in range(len(day_name)):
        db_entry = s.query(User_Weekday_Availability).filter_by(user_id=user_id, weekday_id=i).first()
        if not db_entry:
            db_entry = User_Weekday_Availability(
                user_id=user_id, 
                weekday_id=i, 
                availability=timedelta(seconds=0))
            s.merge(db_entry)
            LogMainSubAgent.agent_steps(f"\t---------Initialized {day_name[i]}.---------")
    return None

# Convert output from the agent to SQL models.
def update_user_availability(s, user_id, weekday_availability):
    # Update each availability entry to the database.
    for i in weekday_availability:
        db_entry = User_Weekday_Availability(
            user_id=user_id, 
            weekday_id=i["weekday_id"], 
            availability=timedelta(seconds=i["availability"]))
        s.merge(db_entry)
    return None