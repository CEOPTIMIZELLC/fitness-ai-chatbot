from app.models import User_Equipment

from .base import BaseRetriever

# ----------------------------------------- User Equipment -----------------------------------------

focus_name = "equipment"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name

    @classmethod
    def item_query(cls, user_id, item_id):
        return (
            User_Equipment.query
            .filter(
                User_Equipment.user_id == user_id, 
                User_Equipment.id == item_id
            )
            .first()
        )

    @classmethod
    def item_list_query(cls, user_id):
        return (
            User_Equipment.query
            .filter(
                User_Equipment.user_id == user_id
            )
            .all()
        )