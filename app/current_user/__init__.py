from flask import Blueprint

current_user = Blueprint('current_user', __name__)

from . import routes