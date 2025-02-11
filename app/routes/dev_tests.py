from random import randrange
from flask import request, jsonify, redirect, url_for, current_app
from flask_cors import CORS
from sqlalchemy import text

import json

#from app.models import Users, Fitness, User_Fitness, Exercises, Exercise_Fitness

from app import db

from . import dev_tests_bp as dev_tests

from ..helper_functions.table_schema_cache import get_database_schema
from ..helper_functions.sql import sql_app
from ..helper_functions.table_context_parser import context_retriever_app

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
@dev_tests.route('/retrieve_db_schema', methods=['GET','POST'])
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

    # Populate equipment.
    from app.existing_data.equipment import equipment
    db.session.add_all(equipment)
    db.session.commit()

    from app.existing_data.user_equipment import user_equipment
    db.session.add_all(user_equipment)
    db.session.commit()

    current_app.table_schema = get_database_schema(db)

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


# Testing for the SQL to add and check training equipment.
@dev_tests.route('/test_equipment_sql', methods=['GET'])
def test_equipment_sql():
    results = {}
    user_question_1 = "Create a new user equipment for my new barbell that weighs 4 kilograms."
    result_1 = sql_app.invoke({"question": user_question_1, "attempts": 0})
    results["result_1"] = result_1["query_result"]
    print("Result:", result_1["query_result"])
    print("")
    
    user_question_2 = "Create a new user equipment for my new treadmill that is 20 centimeters long."
    result_2 = sql_app.invoke({"question": user_question_2, "attempts": 0})
    results["result_2"] = result_2["query_result"]
    print("Result:", result_2["query_result"])
    print("")

    user_question_3 = "Show me my training equipment."
    result_3 = sql_app.invoke({"question": user_question_3, "attempts": 0})
    results["result_3"] = result_3["query_result"]
    print("Result:", result_3["query_result"])
    print("")

    user_question_4 = "Create a new user training equipment for my new treadmill."
    result_4 = sql_app.invoke({"question": user_question_4, "attempts": 0})
    results["result_4"] = result_4["query_result"]
    print("Result:", result_4["query_result"])
    print("")

    user_question_5 = "Show me my training equipment."
    result_5 = sql_app.invoke({"question": user_question_5, "attempts": 0})
    results["result_5"] = result_5["query_result"]
    print("Result:", result_5["query_result"])
    print("")

    return results



# Testing for the SQL to add and check training equipment.
@dev_tests.route('/test_equipment_context', methods=['GET'])
def test_equipment_sql_context():
    results = {}
    
    user_question_1 = "Create a new user equipment for my new barbell that weighs 4 kilograms."
    result_1 = context_retriever_app.invoke({"question": user_question_1, "attempts": 0})
    results["result_1"] = {
        "subjects": result_1["subjects"], 
        "results": result_1["query_result"]}
    print("Subjects:", result_1["subjects"])
    print("Result:", result_1["query_result"])
    print("")
    
    user_question_2 = "Show me my training equipment."
    result_2 = context_retriever_app.invoke({"question": user_question_2, "attempts": 0})
    results["result_2"] = {
        "subjects": result_2["subjects"], 
        "results": result_2["query_result"]}
    print("Subjects:", result_2["subjects"])
    print("Result:", result_2["query_result"])
    print("")

    user_question_3 = "Show me if I am able to do weight lifting."
    result_3 = context_retriever_app.invoke({"question": user_question_3, "attempts": 0})
    results["result_3"] = {
        "subjects": result_3["subjects"], 
        "results": result_3["query_result"]}
    print("Subjects:", result_3["subjects"])
    print("Result:", result_3["query_result"])
    print("")
    

    user_question_4 = "Do I have the equipment available for me to do weight lifting?"
    result_4 = context_retriever_app.invoke({"question": user_question_4, "attempts": 0})
    results["result_4"] = {
        "subjects": result_4["subjects"], 
        "results": result_4["query_result"]}
    print("Subjects:", result_4["subjects"])
    print("Result:", result_4["query_result"])
    print("")

    user_question_5 = "Show me if I have the equipment available to do weight lifting."
    result_5 = context_retriever_app.invoke({"question": user_question_5, "attempts": 0})
    results["result_5"] = {
        "subjects": result_5["subjects"], 
        "results": result_5["query_result"]}
    print("Subjects:", result_5["subjects"])
    print("Result:", result_5["query_result"])
    print("")

    return results