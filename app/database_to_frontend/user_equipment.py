from app.models import User_Equipment

from .base import BaseRetriever

# ----------------------------------------- User Equipment -----------------------------------------

focus_name = "equipment"

class ItemRetriever(BaseRetriever):
    focus_name = focus_name
    searched_table = User_Equipment