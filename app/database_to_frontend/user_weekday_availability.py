from flask import jsonify

from app.models import User_Weekday_Availability
from app.common_table_queries.availability import currently_active_item as current_item
from app.utils.type_conversion import convert_value_and_alter_to_timedelta

from .base import BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- User Weekday Availability -----------------------------------------

focus_name = "availability"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Weekday_Availability

    @classmethod
    def filter_preformatting(cls, filters):
        #filters = cls.filter_preformatting_bounds(convert_value_and_alter_to_timedelta, filters, "availability")
        convert_value_and_alter_to_timedelta(filters, "availability")
        convert_value_and_alter_to_timedelta(filters, "availability_min")
        convert_value_and_alter_to_timedelta(filters, "availability_max")
        return filters

    @classmethod
    def construct_query_filters(cls, filters):
        query_filters = []

        # ID Filters
        query_filters = cls.add_id_filter(query_filters, filters, "weekday_id", User_Weekday_Availability.weekday_id)

        # Value Filters
        query_filters = cls.add_bound_to_filter(query_filters, filters, "availability", User_Weekday_Availability.availability)

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