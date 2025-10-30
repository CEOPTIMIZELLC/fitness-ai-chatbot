from flask import jsonify

from app.models import (
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days, 
    User_Workout_Exercises
)

from app.common_table_queries.phase_components import currently_active_item as current_parent

from .base import SchedulerBaseRetriever as BaseRetriever, BaseCurrentRetriever

# ----------------------------------------- Workout Exercises -----------------------------------------

focus_name = "workout_schedule"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Workout_Exercises

    @classmethod
    def base_item_query(cls):
        return (
            User_Workout_Exercises.query
            .join(User_Workout_Days)
            .join(User_Microcycles)
            .join(User_Mesocycles)
            .join(User_Macrocycles)
        )

    @classmethod
    def construct_query_filters(cls, filters):
        query_filters = []

        # ID Filters
        query_filters = cls.add_id_filter(query_filters, filters, "id", User_Workout_Exercises.id)
        query_filters = cls.add_id_filter(query_filters, filters, "phase_component_id", User_Workout_Exercises.phase_component_id)
        query_filters = cls.add_id_filter(query_filters, filters, "bodypart_id", User_Workout_Exercises.bodypart_id)
        query_filters = cls.add_id_filter(query_filters, filters, "exercise_id", User_Workout_Exercises.exercise_id)
        return query_filters

class CurrentRetriever(BaseCurrentRetriever):
    focus_name = focus_name

    @classmethod
    def current_parent(cls, user_id):
        return current_parent(user_id)

    @classmethod
    def retrieve_children(cls, parent_item):
        return parent_item.exercises

    # Retrieve user's current item.
    @classmethod
    def read_current_item(cls, user_id):
        return jsonify({"status": "error", "message": "This category doesn't have a single active item."}), 404

