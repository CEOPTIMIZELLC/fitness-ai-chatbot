from app.main_sub_agents.user_microcycles import create_microcycle_agent as create_agent
from app.database_to_frontend.user_microcycles import ItemRetriever, CurrentRetriever
from .blueprint_factories.subagent_items import *

# ----------------------------------------- User Microcycles -----------------------------------------

item_name = "user_microcycles"
focus_name = "microcycle"

bp = create_subagent_crud_blueprint(
    name = item_name, 
    url_prefix = "/" + item_name, 
    item_class = ItemRetriever
)
bp = add_current_retrievers_to_subagent_crud_blueprint(
    bp = bp, 
    item_class = CurrentRetriever
)
bp = add_test_retrievers_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = focus_name, 
    agent_creation_caller = create_agent
)
bp = add_initializer_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = focus_name, 
    agent_creation_caller = create_agent
)