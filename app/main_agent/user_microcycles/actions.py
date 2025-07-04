from config import verbose
from flask import Blueprint, abort
from flask_login import current_user
from datetime import timedelta

from app import db
from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

from app.utils.common_table_queries import current_mesocycle, current_microcycle

# ----------------------------------------- User Microcycles -----------------------------------------

def delete_old_children(mesocycle_id):
    db.session.query(User_Microcycles).filter_by(mesocycle_id=mesocycle_id).delete()
    if verbose:
        print("Successfully deleted")

class MicrocycleActions:
    # Retrieve current user's microcycles
    @staticmethod
    def get_user_list():
        user_microcycles = User_Microcycles.query.join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=current_user.id).all()
        return [user_microcycle.to_dict() 
                for user_microcycle in user_microcycles]

    # Retrieve user's current mesocycle's microcycles
    @staticmethod
    def get_user_current_list():
        user_mesocycle = current_mesocycle(current_user.id)
        if not user_mesocycle:
            abort(404, description="No active mesocycle found.")
        user_microcycles = user_mesocycle.microcycles
        return [user_microcycle.to_dict() 
                for user_microcycle in user_microcycles]

    # Retrieve user's current microcycle
    @staticmethod
    def read_user_current_element():
        user_microcycle = current_microcycle(current_user.id)
        if not user_microcycle:
            abort(404, description="No active microcycle found.")
        return user_microcycle.to_dict()

    # Gives four microcycles for mesocycle.
    @staticmethod
    def scheduler():
        user_mesocycle = current_mesocycle(current_user.id)
        if not user_mesocycle:
            abort(404, description="No active mesocycle found.")

        delete_old_children(user_mesocycle.id)

        # Each microcycle must last 1 week.
        microcycle_duration = timedelta(weeks=1)

        # Find how many one week microcycles will be present in the mesocycle
        microcycle_count = user_mesocycle.duration.days // microcycle_duration.days
        microcycle_start = user_mesocycle.start_date

        # Create a microcycle for each week in the mesocycle.
        microcycles = []
        for i in range(microcycle_count):
            microcycle_end = microcycle_start + microcycle_duration
            new_microcycle = User_Microcycles(
                mesocycle_id = user_mesocycle.id,
                order = i+1,
                start_date = microcycle_start,
                end_date = microcycle_end,
            )

            microcycles.append(new_microcycle)

            # Shift the start of the next microcycle to be the end of the current.
            microcycle_start = microcycle_end

        db.session.add_all(microcycles)
        db.session.commit()

        result = []
        for microcycle in microcycles:
            result.append(microcycle.to_dict())
        return result

