from flask import jsonify

from app.models import User_Macrocycles 

class BaseRetriever():
    focus_name = ""
    searched_table = User_Macrocycles

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


class SchedulerBaseRetriever(BaseRetriever):
    # Query to find a specific item belonging to a user.
    # The user macrocycle's user id determines whether its children belong to the user.
    @classmethod
    def item_query(cls, user_id, item_id):
        return (
            cls.base_item_query()
            .filter(
                User_Macrocycles.user_id == user_id, 
                cls.searched_table.id == item_id
            )
            .first()
        )

    # Query to find all items belonging to a user.
    # The user macrocycle's user id determines whether its children belong to the user.
    @classmethod
    def item_list_query(cls, user_id):
        return (
            cls.base_item_query()
            .filter(
                User_Macrocycles.user_id == user_id
            )
            .all()
        )


class BaseCurrentRetriever():
    focus_name = ""

    @classmethod
    def current_parent(cls, user_id):
        pass

    @classmethod
    def retrieve_children(cls, parent_item):
        pass

    # Retrieve user's list of items for the current parent.
    @classmethod
    def list_items_from_current_parent(cls, user_id):
        parent_item = cls.current_parent(user_id)
        if not parent_item:
            return jsonify({"status": "error", "message": "No active parent found."}), 404

        schedule_items = cls.retrieve_children(parent_item)

        result = [
            schedule_item.to_dict() 
            for schedule_item in schedule_items
        ]

        return jsonify({"status": "success", f"user_{cls.focus_name}": result}), 200

    @classmethod
    def current_item(cls, user_id):
        pass

    # Retrieve user's current item.
    @classmethod
    def read_current_item(cls, user_id):
        schedule_item = cls.current_item(user_id)
        if not schedule_item:
            return jsonify({"status": "error", "message": "No active item found."}), 404
        return jsonify({"status": "success", f"user_{cls.focus_name}": schedule_item.to_dict()}), 200


