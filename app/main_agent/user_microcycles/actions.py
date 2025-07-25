from logging_config import LogMainSubAgent
from flask import abort
from flask_login import current_user
from datetime import timedelta

from app import db
from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

from app.utils.common_table_queries import current_mesocycle, current_microcycle

# ----------------------------------------- User Microcycles -----------------------------------------

def delete_old_children(mesocycle_id):
    db.session.query(User_Microcycles).filter_by(mesocycle_id=mesocycle_id).delete()
    LogMainSubAgent.verbose("Successfully deleted")