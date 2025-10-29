from app.main_sub_agents.user_microcycles import create_microcycle_agent as create_agent
from .blueprint_factories import create_subagent_crud_blueprint, add_initializer_to_subagent_crud_blueprint

# ----------------------------------------- User Microcycles -----------------------------------------

bp = create_subagent_crud_blueprint(
    name = 'user_microcycles', 
    focus_name = 'microcycle', 
    url_prefix = '/user_microcycles', 
    agent_creation_caller = create_agent
)
bp = add_initializer_to_subagent_crud_blueprint(
    bp = bp, 
    focus_name = 'microcycle', 
    agent_creation_caller = create_agent
)