from app.models import (
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days
)

from app.common_table_queries.microcycles import currently_active_item as current_parent
from app.common_table_queries.phase_components import currently_active_item as current_item

from .base import SchedulerBaseRetriever as BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- Workout Days -----------------------------------------

focus_name = "phase_component"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Workout_Days

    @classmethod
    def base_item_query(cls):
        return (
            User_Workout_Days.query
            .join(User_Microcycles)
            .join(User_Mesocycles)
            .join(User_Macrocycles)
        )

class CurrentRetriever(BaseCurrentRetriever):
    focus_name = focus_name

    @classmethod
    def current_parent(cls, user_id):
        return current_parent(user_id)

    @classmethod
    def retrieve_children(cls, parent_item):
        return parent_item.workout_days

    @classmethod
    def current_item(cls, user_id):
        return current_item(user_id)