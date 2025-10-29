from app.main_sub_agents.user_weekdays_availability import create_availability_agent as create_agent

from app.common_table_queries.availability import currently_active_item as current_weekday_availability

from .blueprint_factories import create_subagent_crud_blueprint, add_initializer_to_subagent_crud_blueprint

# ----------------------------------------- User Weekday Availability -----------------------------------------

bp = create_subagent_crud_blueprint(
    name = 'user_weekday_availability', 
    focus_name = 'availability', 
    url_prefix = '/user_weekday_availability', 
    agent_creation_caller = create_agent
)
bp = add_initializer_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = 'availability', 
    agent_creation_caller = create_agent
)