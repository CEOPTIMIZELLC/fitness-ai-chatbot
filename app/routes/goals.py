from random import randrange
from flask import request, jsonify, redirect, url_for, current_app, Blueprint
from flask_cors import CORS
from sqlalchemy import text

import json

#from app.models import Users, Fitness, User_Fitness, Exercises, Exercise_Fitness

from app import db
from app.models import table_object

bp = Blueprint('goals', __name__)

from app.agents.goals import goal_app

# ----------------------------------------- Goal Tests -----------------------------------------


# Testing for the SQL to add and check training equipment.
@bp.route('/goal_classification', methods=['GET'])
def goal_classification():
    results = {}
    
    user_goal = "Create a new user equipment for my new barbell that weighs 4 kilograms."
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_1"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")

    
    user_goal = "I would like to do a push up."
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_2"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")

    user_goal = "I would like to be ready for the soccer championship."
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_3"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")
    

    user_goal = "Am I ready for the soccker championship this year?"
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_4"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")

    user_goal = "I would like to weight 100 pounds."
    result_temp = goal_app.invoke({"new_goal": user_goal, "attempts": 0})
    results["result_5"] = {
        "new_goal": user_goal,
        "goal_classification": result_temp["goal_class"],
        "goal_id": result_temp["goal_id"]}
    print(f"Result: '{result_temp["goal_class"]}' with id of '{str(result_temp["goal_id"])}'")
    print("")
    
    return results

