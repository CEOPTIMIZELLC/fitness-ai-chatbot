from app.models import User_Macrocycles, User_Mesocycles

from app.common_table_queries.macrocycles import currently_active_item as current_parent
from app.common_table_queries.mesocycles import currently_active_item as current_item

from .base import SchedulerBaseRetriever as BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- User Mesocycles -----------------------------------------

focus_name = "mesocycle"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Mesocycles

    @classmethod
    def base_item_query(cls):
        return (
            User_Mesocycles.query
            .join(User_Macrocycles)
        )

class CurrentRetriever(BaseCurrentRetriever):
    focus_name = focus_name

    @classmethod
    def current_parent(cls, user_id):
        return current_parent(user_id)

    @classmethod
    def retrieve_children(cls, parent_item):
        return parent_item.mesocycles

    @classmethod
    def current_item(cls, user_id):
        return current_item(user_id)