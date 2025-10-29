from app.main_sub_agents.user_microcycles import create_microcycle_agent as create_agent
from app.database_to_frontend.user_microcycles import ItemRetriever, CurrentRetriever
from .blueprint_factories.subagent_items import create_item_blueprint

# ----------------------------------------- User Microcycles -----------------------------------------

item_name = "user_microcycles"
focus_name = "microcycle"

bp = create_item_blueprint(
    item_name, focus_name, 
    item_retriever = ItemRetriever, 
    current_retriever = CurrentRetriever, 
    create_agent = create_agent, 
    add_test_retrievers = True, 
    add_initializers = True
)