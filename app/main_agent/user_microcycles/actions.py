from app.logging_config import LogMainSubAgent

from app import db
from app.models import User_Microcycles

# ----------------------------------------- User Microcycles -----------------------------------------

def delete_old_children(mesocycle_id):
    db.session.query(User_Microcycles).filter_by(mesocycle_id=mesocycle_id).delete()
    LogMainSubAgent.verbose("Successfully deleted")