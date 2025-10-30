from app.models import User_Equipment

from .base import BaseRetriever

# ----------------------------------------- User Equipment -----------------------------------------

focus_name = "equipment"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Equipment

    @classmethod
    def construct_query_filters(cls, filters):
        query_filters = []

        # ID Filters
        query_filters = cls.add_id_filter(query_filters, filters, "id", User_Equipment.id)
        query_filters = cls.add_id_filter(query_filters, filters, "equipment_id", User_Equipment.equipment_id)

        # Value Filters
        query_filters = cls.add_bound_to_filter(query_filters, filters, "measurement", User_Equipment.measurement)

        return query_filters