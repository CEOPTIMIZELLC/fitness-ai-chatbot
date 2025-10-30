from flask import jsonify

from app.models import User_Macrocycles
from app.common_table_queries.macrocycles import currently_active_item as current_item
from app.utils.type_conversion import convert_value_and_alter_to_date

from .base import BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- User Macrocycles -----------------------------------------

focus_name = "macrocycle"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Macrocycles

    @classmethod
    def filter_preformatting(cls, filters):
        convert_value_and_alter_to_date(filters, "start_date")
        convert_value_and_alter_to_date(filters, "start_date_min")
        convert_value_and_alter_to_date(filters, "start_date_max")
        convert_value_and_alter_to_date(filters, "end_date")
        convert_value_and_alter_to_date(filters, "end_date_min")
        convert_value_and_alter_to_date(filters, "end_date_max")
        return filters

    @classmethod
    def construct_query_filters(cls, filters):
        query_filters = []

        # ID Filters
        query_filters = cls.add_id_filter(query_filters, filters, "id", User_Macrocycles.id)
        query_filters = cls.add_id_filter(query_filters, filters, "goal_id", User_Macrocycles.goal_id)

        # Value Filters
        query_filters = cls.add_bound_to_filter(query_filters, filters, "start_date", User_Macrocycles.start_date)
        query_filters = cls.add_bound_to_filter(query_filters, filters, "end_date", User_Macrocycles.end_date)

        return query_filters

class CurrentRetriever(BaseCurrentRetriever):
    focus_name = focus_name

    @classmethod
    def current_item(cls, user_id):
        return current_item(user_id)

    # Retrieve user's list of items for the current parent.
    @classmethod
    def list_items_from_current_parent(cls, user_id):
        return jsonify({"status": "error", "message": "No parent exists for this item."}), 404