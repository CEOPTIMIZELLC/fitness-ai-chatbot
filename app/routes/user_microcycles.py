from flask import Blueprint
from flask_login import login_required

from app.main_sub_agents.user_microcycles import create_microcycle_agent as create_agent

bp = Blueprint('user_microcycles', __name__)

from .blueprint_factories import get_user_list, get_user_current_list, read_user_current, item_initializer, item_initializer_with_parent_id

# ----------------------------------------- User Microcycles -----------------------------------------

# Retrieve current user's microcycles
@bp.route('/', methods=['GET'])
@login_required
def get_user_microcycles_list():
    return get_user_list(focus_name="microcycle", agent_creation_caller=create_agent)

# Retrieve user's current macrocycle's mesocycles
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_mesocycles_list():
    return get_user_current_list(focus_name="microcycle", agent_creation_caller=create_agent)

# Retrieve user's current microcycle
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_microcycle():
    return read_user_current(focus_name="microcycle", agent_creation_caller=create_agent)

# Gives four microcycles for mesocycle.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def microcycle_initializer():
    return item_initializer(focus_name="microcycle", agent_creation_caller=create_agent)

# Gives four microcycles for mesocycle and gives the parent mesocycle a new id.
@bp.route('/<phase_id>', methods=['POST', 'PATCH'])
@login_required
def microcycle_initializer_by_id(phase_id):
    return item_initializer_with_parent_id(focus_name="microcycle", agent_creation_caller=create_agent, parent_id=phase_id)