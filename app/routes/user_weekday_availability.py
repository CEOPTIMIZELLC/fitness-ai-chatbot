from app.main_sub_agents.user_weekdays_availability import create_availability_agent as create_agent
from .blueprint_factories import create_subagent_crud_blueprint

# ----------------------------------------- User Weekday Availability -----------------------------------------

bp = create_subagent_crud_blueprint('user_weekday_availability', 'availability', '/user_weekday_availability', create_agent)