from app.models import (
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days
)

from app.common_table_queries.microcycles import currently_active_item as current_parent
from app.common_table_queries.phase_components import currently_active_item as current_item
from app.utils.type_conversion import convert_value_and_alter_to_date

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

    @classmethod
    def filter_preformatting(cls, filters):
        convert_value_and_alter_to_date(filters, "date")
        convert_value_and_alter_to_date(filters, "date_min")
        convert_value_and_alter_to_date(filters, "date_max")
        return filters

    @classmethod
    def construct_query_filters(cls, filters):
        query_filters = []

        # ID Filters
        query_filters = cls.add_id_filter(query_filters, filters, "id", User_Workout_Days.id)
        query_filters = cls.add_id_filter(query_filters, filters, "microcycle_id", User_Workout_Days.microcycle_id)
        query_filters = cls.add_id_filter(query_filters, filters, "weekday_id", User_Workout_Days.weekday_id)
        query_filters = cls.add_id_filter(query_filters, filters, "loading_system_id", User_Workout_Days.loading_system_id)

        # Value Filters
        query_filters = cls.add_bound_to_filter(query_filters, filters, "date", User_Workout_Days.date)

        return query_filters

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