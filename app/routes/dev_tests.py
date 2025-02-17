from random import randrange
from flask import request, jsonify, redirect, url_for, current_app, Blueprint
from flask_cors import CORS
from sqlalchemy import text

import json

#from app.models import Users, Fitness, User_Fitness, Exercises, Exercise_Fitness

from app import db
from app.models import table_object

bp = Blueprint('dev_tests', __name__)

from app.helper_functions.table_schema_cache import get_database_schema
from app.helper_functions.sql import sql_app
from app.helper_functions.table_context_parser import context_retriever_app

from app.helper_functions.cp_pulp import Main as cp_pulp_main
from app.helper_functions.cp_pulp_equipment_test import Main as cp_pulp_equipment_test_main

# ----------------------------------------- Dev Tests -----------------------------------------

# Testing for the SQL to add and check training equipment.
@bp.route('/test_equipment_sql', methods=['GET'])
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
@bp.route('/test_equipment_context', methods=['GET'])
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




# Testing for constrain programming.
@bp.route('/test_cp_pulp', methods=['GET'])
def test_cp_pulp():
    results = {}
    
    result_1 = cp_pulp_main()
    print("\n\n\n\n\nRESULT")
    print(result_1["output"])
    #results["result_1"] = result_1

    return results

# Testing for constrain programming.
@bp.route('/test_cp_pulp_equipment', methods=['GET'])
def test_cp_pulp_equipment():
    results = {}
    
    result_1 = cp_pulp_equipment_test_main()
    print("\n\n\n\n\nRESULT")
    print(result_1["output"])
    #results["result_1"] = result_1

    return results