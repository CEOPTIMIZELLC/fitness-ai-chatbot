from random import randrange
from flask import request, jsonify, redirect, url_for, current_app
from flask_cors import CORS
from sqlalchemy import text

import json

#from app.models import Users, Fitness, User_Fitness, Exercises, Exercise_Fitness

from app import db

from . import dev_tests_bp as dev_tests

from ..helper_functions.table_schema_cache import retrieve_table_schema
from ..helper_functions.sql import sql_app 

from .auth import register

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
    return inspector.get_table_names()

# Get all table names in the database
@dev_tests.route('/retrieve_table_schema', methods=['GET','POST'])
def get_table_schema():
    return current_app.table_schema

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
    
    current_app.table_schema = retrieve_table_schema(db)

    return "Database CREATED!"


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
@dev_tests.route('/read_table', methods=['GET'])
def read_table():
    if 'table_name' not in request.form:
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400
    table_name = request.form.get("table_name")

    # Make sure that table with the desired name exists.
    if table_name not in get_table_names():
        return jsonify({"status": "error", "message": f"Table with name '{table_name}' does not exist."}), 400

    state = {"sql_query": f"SELECT * FROM {table_name}"}

    execute_sql(state)

    return state



# Table Reader
@dev_tests.route('/test_sql_reader', methods=['GET'])
def test_sql_reader():
    from IPython.display import Image, display

    try:
        display(Image(sql_app.get_graph(xray=True).draw_mermaid_png()))
    except:
        pass


    user_question_1 = "Create a new order for Spaghetti Carbonara."
    result_1 = sql_app.invoke({"question": user_question_1, "attempts": 0})
    print("Result:", result_1["query_result"])

    user_question_2 = "Tell me a joke."
    result_2 = sql_app.invoke({"question": user_question_2, "attempts": 0})
    print("Result:", result_2["query_result"])

    user_question_3 = "Show me my orders"
    result_3 = sql_app.invoke({"question": user_question_3, "attempts": 0})
    print("Result:", result_3["query_result"])


    user_question_1 = "Create a new order for Spaghetti Carbonara."
    result_1 = sql_app.invoke({"question": user_question_1, "attempts": 0})
    print("Result:", result_1["query_result"])

    user_question_2 = "Tell me a joke."
    result_2 = sql_app.invoke({"question": user_question_2, "attempts": 0})
    print("Result:", result_2["query_result"])

    user_question_3 = "Show me my orders"
    result_3 = sql_app.invoke({"question": user_question_3, "attempts": 0})
    print("Result:", result_3["query_result"])
