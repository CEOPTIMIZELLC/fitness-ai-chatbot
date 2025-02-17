from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from . import auth

current_user_bp = Blueprint('current_user', __name__)

from . import current_user

dev_tests_bp = Blueprint('dev_tests', __name__)

from . import dev_tests

database_manipulation_bp = Blueprint('database_manipulation', __name__)

from . import database_manipulation