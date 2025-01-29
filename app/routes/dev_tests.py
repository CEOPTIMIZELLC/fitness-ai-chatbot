from random import randrange
from flask import request, jsonify, redirect, url_for
from flask_cors import CORS

#from ..models import Users, Fitness, User_Fitness, Exercises, Exercise_Fitness

from .. import db, TABLE_NAMES_CACHE

from . import dev_tests_bp as dev_tests

from ..helper_functions.table_names_cache import retrieve_table_names

from .auth import register

#from ..auth.routes import register


# ----------------------------------------- Dev Tests -----------------------------------------


def create_db():
    """Creates the database."""
    db.create_all()

def drop_db():
    """Drops the database."""
    db.drop_all()

def recreate_db():
    """Same as running drop_db() and create_db()."""
    drop_db()
    create_db()


# Get all table names in the database
@dev_tests.route('/retrieve_table_names', methods=['GET','POST'])
def get_table_names():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)  # Create an inspector bound to the engine
    #return TABLE_NAMES_CACHE
    return inspector.get_table_names()

# Database initialization
@dev_tests.route('/init_db', methods=['GET','POST'])
def initialize_db():
    
    drop_db()
    create_db()

    if ('email' in request.form 
        and 'password' in request.form 
        and 'password_confirm' in request.form
        and 'first_name' in request.form
        and 'last_name' in request.form
        and 'age' in request.form
        and 'gender' in request.form
        and 'goal' in request.form):
        register()
    
    global TABLE_NAMES_CACHE
    TABLE_NAMES_CACHE = retrieve_table_names()

    return "Database CREATED!"