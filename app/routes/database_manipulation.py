from flask import request, jsonify, current_app, Blueprint

from app import db
from app.models import table_object

bp = Blueprint('database_manipulation', __name__)

from app.helper_functions.table_schema_cache import get_database_schema
from app.routes.auth import register

# ----------------------------------------- Database Manipulation -----------------------------------------


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
@bp.route('/retrieve_table_names', methods=['GET','POST'])
def get_table_names():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)  # Create an inspector bound to the engine
    return inspector.get_table_names()

# Get all table names in the database
@bp.route('/retrieve_db_schema', methods=['GET','POST'])
def get_table_schema():
    return current_app.table_schema

# Database initialization
@bp.route('/init_db', methods=['GET','POST'])
def initialize_db():
    
    drop_db()
    create_db()

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
        register()
    
        '''from app.existing_data.user_equipment import user_equipment
        db.session.add_all(user_equipment)
        db.session.commit()'''

    current_app.table_schema = get_database_schema(db)

    return "Database CREATED!"

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
    return {"status": "success", "results": final_result}, 200

# Table Reader
@bp.route('/read_table', methods=['GET'])
def read_table():
    if 'table_name' not in request.form:
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400
    table_name = request.form.get("table_name")

    # Make sure that table with the desired name exists.
    if table_name not in get_table_names():
        return jsonify({"status": "error", "message": f"Table with name '{table_name}' does not exist."}), 400

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
    return {"status": "success", "results": result}, 200