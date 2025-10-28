from app.main_sub_agents.user_microcycles import create_microcycle_agent as create_agent
from .blueprint_factories import create_subagent_crud_blueprint

# ----------------------------------------- User Microcycles -----------------------------------------

bp = create_subagent_crud_blueprint('user_microcycles', 'microcycle', '/user_microcycles', create_agent)