from flask import jsonify

from app.models import User_Macrocycles
from app.common_table_queries.macrocycles import currently_active_item as current_item

from .base import BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- User Macrocycles -----------------------------------------

focus_name = "macrocycle"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name

    @classmethod
    def item_query(cls, user_id, item_id):
        return (
            User_Macrocycles.query
            .filter(
                User_Macrocycles.user_id == user_id, 
                User_Macrocycles.id == item_id
            )
            .first()
        )

    @classmethod
    def item_list_query(self, user_id):
        return (
            User_Macrocycles.query
            .filter_by(user_id=user_id)
            .all()
        )

class CurrentRetriever(BaseCurrentRetriever):
    focus_name = focus_name

    @classmethod
    def current_item(self, user_id):
        return current_item(user_id)

    # Retrieve user's list of items for the current parent.
    @classmethod
    def list_items_from_current_parent(cls, user_id):
        return jsonify({"status": "error", "message": "No parent exists for this item."}), 404