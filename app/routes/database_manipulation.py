from logging_config import LogDBInit
from flask import request, jsonify, current_app, Blueprint, abort

from app import db
from app.models import table_object

from app.utils.table_schema_cache import get_database_schema
from app.routes.auth import register

bp = Blueprint('database_manipulation', __name__)

# ----------------------------------------- Database Manipulation -----------------------------------------


# def create_db():
#     """Creates the database."""
#     db.create_all()

# def drop_db():
#     """Drops the database."""
#     db.drop_all()

# def recreate_db():
#     """Same as running drop_db() and create_db()."""
#     drop_db()
#     create_db()


# Get all table names in the database
@bp.route('/retrieve_table_names', methods=['GET','POST'])
def get_table_names():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)  # Create an inspector bound to the engine
    return inspector.get_table_names()

# Get all table names in the database
@bp.route('/retrieve_db_schema', methods=['GET','POST'])
def get_table_schema():
    return current_app.table_schema

# Database drop
@bp.route('/drop_db', methods=['GET','POST'])
def drop_db():
    """Drops the database."""
    LogDBInit.introductions(f"Dropping old database.")
    db.drop_all()

    return jsonify({"status": "success", "message": "Database DROPPED!"}), 200

# Database creation
@bp.route('/create_db', methods=['GET','POST'])
def create_db():
    """Creates the database."""
    LogDBInit.introductions(f"Initializing database.")
    db.create_all()

    from app.existing_data.import_existing_data import Main as import_data_main

    import_data_main("OPT Phase Breakdown.xlsx")

    if ('email' in request.form 
        and 'password' in request.form 
        and 'password_confirm' in request.form
        and 'first_name' in request.form
        and 'last_name' in request.form
        and 'age' in request.form
        and 'gender' in request.form
        and 'goal' in request.form):
        LogDBInit.introductions(f"Adding User.")
        register()
    
        from app.existing_data.user_equipment import get_default_user_equipment
        user_equipment = get_default_user_equipment()
        if user_equipment:
            LogDBInit.introductions(f"Adding User equipment.")
            db.session.add_all(user_equipment)
            db.session.commit()
        LogDBInit.introductions(f"User added.")

    current_app.table_schema = get_database_schema(db)

    return jsonify({"status": "success", "message": "Database CREATED!"}), 200

# Database reinitialization
@bp.route('/init_db', methods=['GET','POST'])
def initialize_db():
    LogDBInit.introductions(f"Dropping old database and reinitializing with new database structure.")

    results = []
    
    results.append(drop_db()[0].get_json()["message"])
    results.append(create_db()[0].get_json()["message"])
    return jsonify({"status": "success", "message": results}), 200

# Table Reader
@bp.route('/read_all_tables', methods=['GET'])
def read_all_tables():

    # Make sure that table with the desired name exists.
    table_names = get_table_names()

    final_result = {}

    for table_name in table_names:
        query_result = db.session.query(table_object(table_name=table_name)).all()
        result = []
        for elem in query_result: 
            result.append(elem.to_dict())
        print(f"\n\nTable: {table_name}")
        for i in result:
            print(i)
        final_result[table_name] = result
    return jsonify({"status": "success", "results": final_result}), 200

# Table Reader
@bp.route('/read_table', methods=['GET'])
def read_table():
    if 'table_name' not in request.form:
        abort(400, description="Please fill out the form!")
    table_name = request.form.get("table_name")

    # Make sure that table with the desired name exists.
    if table_name not in get_table_names():
        abort(400, description=f"Table with name '{table_name}' does not exist.")

    '''
    state = {"sql_query": f"SELECT * FROM {table_name}"}
    execute_sql(state)
    return state
    '''

    query_result = db.session.query(table_object(table_name=table_name)).all()
    result = []
    for elem in query_result: 
        result.append(elem.to_dict())
    print(f"Table: {table_name}")
    for i in result:
        print(i)
    return jsonify({"status": "success", "results": result}), 200