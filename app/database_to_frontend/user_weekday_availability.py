from flask import jsonify

from app.models import User_Weekday_Availability
from app.common_table_queries.availability import currently_active_item as current_item

from .base import BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- User Weekday Availability -----------------------------------------

focus_name = "availability"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Weekday_Availability

class CurrentRetriever(BaseCurrentRetriever):
    focus_name = focus_name

    @classmethod
    def current_item(cls, user_id):
        return current_item(user_id)

    # Retrieve user's list of items for the current parent.
    @classmethod
    def list_items_from_current_parent(cls, user_id):
        return jsonify({"status": "error", "message": "No parent exists for this item."}), 404