from app.main_sub_agents.user_weekdays_availability import create_availability_agent as create_agent
from app.database_to_frontend.user_weekday_availability import ItemRetriever, CurrentRetriever
from .blueprint_factories import create_subagent_crud_blueprint, add_current_retrievers_to_subagent_crud_blueprint, add_test_retrievers_to_subagent_crud_blueprint, add_initializer_to_subagent_crud_blueprint

# ----------------------------------------- User Weekday Availability -----------------------------------------

bp = create_subagent_crud_blueprint(
    name = 'user_weekday_availability', 
    url_prefix = '/user_weekday_availability', 
    item_class = ItemRetriever
)
bp = add_current_retrievers_to_subagent_crud_blueprint(
    bp = bp, 
    item_class = CurrentRetriever
)
bp = add_test_retrievers_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = 'availability', 
    agent_creation_caller = create_agent
)
bp = add_initializer_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = 'availability', 
    agent_creation_caller = create_agent
)