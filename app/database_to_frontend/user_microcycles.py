from app.models import User_Macrocycles, User_Mesocycles, User_Microcycles

from app.common_table_queries.mesocycles import currently_active_item as current_parent
from app.common_table_queries.microcycles import currently_active_item as current_item

from .base import BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- User Microcycles -----------------------------------------

focus_name = "microcycle"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name

    @classmethod
    def item_query(cls, user_id, item_id):
        return (
            User_Microcycles.query
            .join(User_Mesocycles)
            .join(User_Macrocycles)
            .filter(
                User_Macrocycles.user_id == user_id, 
                User_Microcycles.id == item_id
            )
            .first()
        )

    @classmethod
    def item_list_query(self, user_id):
        return (
            User_Microcycles.query
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
        return parent_item.microcycles

    @classmethod
    def current_item(self, user_id):
        return current_item(user_id)