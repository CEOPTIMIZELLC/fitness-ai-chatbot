from app.models import User_Macrocycles, User_Mesocycles

from app.common_table_queries.macrocycles import currently_active_item as current_parent
from app.common_table_queries.mesocycles import currently_active_item as current_item
from app.utils.type_conversion import convert_value_and_alter_to_date

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
        query_filters = cls.add_id_filter(query_filters, filters, "id", User_Mesocycles.id)
        query_filters = cls.add_id_filter(query_filters, filters, "macrocycle_id", User_Mesocycles.macrocycle_id)
        query_filters = cls.add_id_filter(query_filters, filters, "phase_id", User_Mesocycles.phase_id)

        # Value Filters
        query_filters = cls.add_is_equal_to_filter(query_filters, filters, "is_goal_phase", User_Mesocycles.is_goal_phase)
        query_filters = cls.add_bound_to_filter(query_filters, filters, "start_date", User_Mesocycles.start_date)
        query_filters = cls.add_bound_to_filter(query_filters, filters, "end_date", User_Mesocycles.end_date)

        return query_filters

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