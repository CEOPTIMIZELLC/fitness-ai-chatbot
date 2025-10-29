from app.main_sub_agents.user_weekdays_availability import create_availability_agent as create_agent
from app.database_to_frontend.user_weekday_availability import ItemRetriever, CurrentRetriever
from .blueprint_factories.subagent_items import create_item_blueprint

# ----------------------------------------- User Weekday Availability -----------------------------------------

item_name = "user_weekday_availability"
focus_name = "availability"

bp = create_item_blueprint(
    item_name, focus_name, 
    item_retriever = ItemRetriever, 
    current_retriever = CurrentRetriever, 
    create_agent = create_agent, 
    add_test_retrievers = True, 
    add_initializers = True
)