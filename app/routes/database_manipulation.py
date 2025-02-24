from random import randrange
from flask import request, jsonify, current_app, Blueprint
from flask_cors import CORS
from sqlalchemy import text

import json

#from app.models import Users, Fitness, User_Fitness, Exercises, Exercise_Fitness

from app import db
from app.models import table_object

bp = Blueprint('database_manipulation', __name__)

from app.helper_functions.table_schema_cache import get_database_schema

from app.routes.auth import register

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

    if ('email' in request.form 
        and 'password' in request.form 
        and 'password_confirm' in request.form
        and 'first_name' in request.form
        and 'last_name' in request.form
        and 'age' in request.form
        and 'gender' in request.form
        and 'goal' in request.form):
        register()

    # Populate items.
    from app.existing_data.goals import goals
    db.session.add_all(goals)
    db.session.commit()

    from app.existing_data.phases import phases
    db.session.add_all(phases)
    db.session.commit()

    from app.existing_data.equipment import equipment
    db.session.add_all(equipment)
    db.session.commit()

    from app.existing_data.user_equipment import user_equipment
    db.session.add_all(user_equipment)
    db.session.commit()

    from app.existing_data.exercises import exercises
    db.session.add_all(exercises)
    db.session.commit()

    from app.existing_data.exercise_equipment import exercise_equipment
    db.session.add_all(exercise_equipment)
    db.session.commit()

    current_app.table_schema = get_database_schema(db)

    return "Database CREATED!"


def execute_sql_single_column(state):
    sql_query = state["sql_query"].strip()
    print(f"Executing SQL query: {sql_query}")
    try:
        result = db.session.execute(text(sql_query))
        rows = result.fetchall()
        if rows:
            state["query_rows"] = [list(i)[0] for i in rows]
            print(f"Raw SQL Query Result: {state['query_rows']}")
            # Format the result for readability
            data = "; ".join([f"{row}" for row in state["query_rows"]])
            formatted_result = f"{data}"
        else:
            state["query_rows"] = []
            formatted_result = "No results found."
        state["query_result"] = formatted_result
        state["sql_error"] = False
        print("SQL SELECT query executed successfully.")
    except Exception as e:
        state["query_result"] = f"Error executing SQL query: {str(e)}"
        state["sql_error"] = True
        print(f"Error executing SQL query: {str(e)}")
    return state

def execute_sql(state):
    sql_query = state["sql_query"].strip()
    print(f"Executing SQL query: {sql_query}")
    try:
        result = db.session.execute(text(sql_query))
        if sql_query.lower().startswith("select"):
            rows = result.fetchall()
            columns = result.keys()
            if rows:
                header = ", ".join(columns)
                state["query_rows"] = [dict(zip(columns, row)) for row in rows]
                print(f"Raw SQL Query Result: {state['query_rows']}")
                # Format the result for readability
                data = "; ".join([f"{row.get('food_name', row.get('name'))} for ${row.get('price', row.get('food_price'))}" for row in state["query_rows"]])
                formatted_result = f"{header}\n{data}"
            else:
                state["query_rows"] = []
                formatted_result = "No results found."
            state["query_result"] = formatted_result
            state["sql_error"] = False
            print("SQL SELECT query executed successfully.")
        else:
            db.session.commit()
            state["query_result"] = "The action has been successfully completed."
            state["sql_error"] = False
            print("SQL command executed successfully.")
    except Exception as e:
        state["query_result"] = f"Error executing SQL query: {str(e)}"
        state["sql_error"] = True
        print(f"Error executing SQL query: {str(e)}")
    return state

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
    print(result)
    return {"status": "success", "results": result}, 200

# Table Reader
@bp.route('/read_table_sql_names', methods=['GET'])
def read_table_sql_names():
    if 'table_name' not in request.form:
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400
    table_name = request.form.get("table_name")

    # Make sure that table with the desired name exists.
    if table_name not in get_table_names():
        return jsonify({"status": "error", "message": f"Table with name '{table_name}' does not exist."}), 400
    
    state = {"sql_query": f"SELECT name FROM {table_name}"}
    execute_sql_single_column(state)
    return state
