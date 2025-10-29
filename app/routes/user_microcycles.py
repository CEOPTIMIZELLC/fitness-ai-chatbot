from app.main_sub_agents.user_microcycles import create_microcycle_agent as create_agent
from app.database_to_frontend.user_microcycles import ItemRetriever, CurrentRetriever
from .blueprint_factories.subagent_items import *

# ----------------------------------------- User Microcycles -----------------------------------------

bp = create_subagent_crud_blueprint(
    name = 'user_microcycles', 
    url_prefix = '/user_microcycles', 
    item_class = ItemRetriever
)
bp = add_current_retrievers_to_subagent_crud_blueprint(
    bp = bp, 
    item_class = CurrentRetriever
)
bp = add_test_retrievers_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = 'microcycle', 
    agent_creation_caller = create_agent
)
bp = add_initializer_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = 'microcycle', 
    agent_creation_caller = create_agent
)