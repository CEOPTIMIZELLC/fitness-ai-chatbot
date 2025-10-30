from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

from app.common_table_queries.mesocycles import currently_active_item as current_parent
from app.common_table_queries.microcycles import currently_active_item as current_item

from .base import SchedulerBaseRetriever as BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- User Microcycles -----------------------------------------

focus_name = "microcycle"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Microcycles

    @classmethod
    def base_item_query(cls):
        return (
            User_Microcycles.query
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
        return parent_item.microcycles

    @classmethod
    def current_item(cls, user_id):
        return current_item(user_id)