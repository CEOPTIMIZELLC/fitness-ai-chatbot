from flask import Blueprint

dev_tests = Blueprint('dev_tests', __name__)

from . import routes