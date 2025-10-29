from app.models import (
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days
)

from app.common_table_queries.microcycles import currently_active_item as current_parent
from app.common_table_queries.phase_components import currently_active_item as current_item

from .base import BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- Workout Days -----------------------------------------

focus_name = "phase_component"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name

    @classmethod
    def item_query(cls, user_id, item_id):
        return (
            User_Workout_Days.query
            .join(User_Microcycles)
            .join(User_Mesocycles)
            .join(User_Macrocycles)
            .filter(
                User_Macrocycles.user_id == user_id, 
                User_Workout_Days.id == item_id
            )
            .first()
        )

    @classmethod
    def item_list_query(self, user_id):
        return (
            User_Workout_Days.query
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
        return parent_item.workout_days

    @classmethod
    def current_item(self, user_id):
        return current_item(user_id)