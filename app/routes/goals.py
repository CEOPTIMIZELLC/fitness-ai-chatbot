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
    
    user_goal_1 = "Create a new user equipment for my new barbell that weighs 4 kilograms."
    result_1 = goal_app.invoke({"new_goal": user_goal_1, "attempts": 0})
    results["result_1"] = {
        "new_goal": user_goal_1,
        "results": result_1["goal_class"]}
    print("Result:", result_1["goal_class"])
    print("")

    
    user_goal_2 = "I would like to do a push up."
    result_2 = goal_app.invoke({"new_goal": user_goal_2, "attempts": 0})
    results["result_2"] = {
        "new_goal": user_goal_2,
        "results": result_2["goal_class"]}
    print("Result:", result_2["goal_class"])
    print("")

    user_goal_3 = "I would like to be ready for the soccer championship."
    result_3 = goal_app.invoke({"new_goal": user_goal_3, "attempts": 0})
    results["result_3"] = {
        "new_goal": user_goal_3,
        "results": result_3["goal_class"]}
    print("Result:", result_3["goal_class"])
    print("")
    

    user_goal_4 = "Am I ready for the soccker championship this year?"
    result_4 = goal_app.invoke({"new_goal": user_goal_4, "attempts": 0})
    results["result_4"] = {
        "new_goal": user_goal_4,
        "results": result_4["goal_class"]}
    print("Result:", result_4["goal_class"])
    print("")

    user_goal_5 = "I would like to weight 100 pounds."
    result_5 = goal_app.invoke({"new_goal": user_goal_5, "attempts": 0})
    results["result_5"] = {
        "new_goal": user_goal_5,
        "results": result_5["goal_class"]}
    print("Result:", result_5["goal_class"])
    print("")
    
    return results

