from flask import jsonify

from app.models import (
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days, 
    User_Workout_Exercises
)

from app.common_table_queries.phase_components import currently_active_item as current_parent

from .base import BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- Workout Exercises -----------------------------------------

focus_name = "workout_schedule"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name

    @classmethod
    def item_query(cls, user_id, item_id):
        return (
            User_Workout_Exercises.query
            .join(User_Workout_Days)
            .join(User_Microcycles)
            .join(User_Mesocycles)
            .join(User_Macrocycles)
            .filter(
                User_Macrocycles.user_id == user_id, 
                User_Workout_Exercises.id == item_id
            )
            .first()
        )

    @classmethod
    def item_list_query(self, user_id):
        return (
            User_Workout_Exercises.query
            .join(User_Workout_Days)
            .join(User_Microcycles)
            .join(User_Mesocycles)
            .join(User_Macrocycles)
            .filter_by(user_id=user_id)
            .all()
        )

class CurrentRetriever(BaseCurrentRetriever):
    focus_name = focus_name

    @classmethod
    def current_parent(self, user_id):
        return current_parent(user_id)

    @classmethod
    def retrieve_children(self, parent_item):
        return parent_item.exercises

    # Retrieve user's current item.
    @classmethod
    def read_current_item(cls, user_id):
        return jsonify({"status": "error", "message": "This category doesn't have a single active item."}), 404

