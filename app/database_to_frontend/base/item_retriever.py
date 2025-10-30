from flask import jsonify

from .utils import FilterHelpers

class BaseRetriever(FilterHelpers):
    focus_name = ""
    searched_table = None

    # Base query that will be called by all other queries.
    @classmethod
    def base_item_query(cls):
        return cls.searched_table.query

    # Query to find a specific item belonging to a user.
    @classmethod
    def item_query(cls, user_id, item_id):
        return (
            cls.base_item_query()
            .filter(
                cls.searched_table.user_id == user_id, 
                cls.searched_table.id == item_id
            )
            .first()
        )

    # Retrieves an item belonging to the user and converts it to a json output.
    @classmethod
    def get_item(cls, user_id, item_id):
        schedule_item = cls.item_query(user_id, item_id)
        if not schedule_item:
            return jsonify({"status": "error", "message": f"No item of {item_id} found for current user."}), 404

        result = schedule_item.to_dict() 
        return jsonify({"status": "success", f"user_{cls.focus_name}": result}), 200

    # Query to find all items belonging to a user.
    @classmethod
    def item_list_query(cls, user_id):
        return (
            cls.base_item_query()
            .filter(
                cls.searched_table.user_id == user_id
            )
            .all()
        )

    # Retrieves all items belonging to the user and converts them to a json output.
    @classmethod
    def list_items(cls, user_id):
        schedule_items = cls.item_list_query(user_id)

        result = [
            schedule_item.to_dict() 
            for schedule_item in schedule_items
        ]

        return jsonify({"status": "success", f"user_{cls.focus_name}": result}), 200

    # Performs preformatting on filtered values that may need to be converted to a different type from the one received by the frontend.
    @classmethod
    def filter_preformatting(cls, filters):
        return filters

    # Constructs the list of filters to be applied.
    @classmethod
    def construct_query_filters(cls, filters):
        return []

    @classmethod
    def item_filter_query(cls, user_id, filters):
        filters = cls.filter_preformatting(filters)
        query_filters = cls.construct_query_filters(filters)
        query_filters.append(cls.searched_table.user_id == user_id)

        return (
            cls.base_item_query()
            .filter(*query_filters)
            .all()
        )

    # Retrieve current user's filtered list of items.
    @classmethod
    def filter_items(cls, user_id, filters):
        schedule_items = cls.item_filter_query(user_id, filters)

        result = [
            schedule_item.to_dict() 
            for schedule_item in schedule_items
        ]

        return jsonify({"status": "success", f"user_{cls.focus_name}": result}), 200
