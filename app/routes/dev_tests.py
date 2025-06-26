from random import randint
from datetime import timedelta, date
from flask import request, jsonify, Blueprint, abort

from flask_login import current_user, login_required

from config import verbose, performance_decay_grace_period
from app import db
from app.utils.sql import sql_app
from app.utils.table_context_parser import context_retriever_app

from app.main_agent_steps import (
    MacrocycleActions, 
    MesocycleActions, 
    MicrocycleActions, 
    MicrocycleSchedulerActions, 
    WorkoutActions, 
    WeekdayAvailabilitySchedulerActions)


bp = Blueprint('dev_tests', __name__)

# ----------------------------------------- Dev Tests -----------------------------------------

def run_segment(segment_class, segment_name=None):
    if verbose and segment_name:
        print(f"\n========================== {segment_name} ==========================")
    result = segment_class.scheduler()
    return result

def run_ai_segment(segment_class, input, segment_name=None):
    if verbose and segment_name:
        print(f"\n========================== {segment_name} ==========================")
    result = segment_class.scheduler(input)
    return result

def run_schedule_segment(segment_class, segment_name=None):
    if verbose and segment_name:
        print(f"\n========================== {segment_name} ==========================")
    result = segment_class.scheduler()
    result["formatted_schedule"] = segment_class.get_formatted_list()
    return result

# Quick check of the entire pipeline
@bp.route('/pipeline', methods=['GET'])
@login_required
def check_pipeline():
    result = {}
    result["user_availability"] = WeekdayAvailabilitySchedulerActions.get_user_list()
    result["user_macrocycles"] = MacrocycleActions.read_user_current_element()
    result["user_mesocycles"] = MesocycleActions.get_formatted_list()
    result["user_microcycles"] = MicrocycleActions.get_user_current_list()
    result["user_planned_microcycle"] = MicrocycleSchedulerActions.get_formatted_list()
    result["user_workout"] = WorkoutActions.get_formatted_list()
    return result

# Quick test of the entire pipeline
@bp.route('/pipeline', methods=['POST'])
@login_required
def run_pipeline():
    # Input is a json.
    data = request.get_json()
    if not data:
        abort(400, description="Invalid request")

    if ('goal' not in data):
        abort(400, description="Please fill out the form!")

    if ('availability' not in data):
        abort(400, description="Please fill out the form!")

    runs = data.get("runs", 1)
    availability = data.get("availability", "")
    goal = data.get("goal", "")
    results = []
    for i in range(1, runs+1):
        result = {}
        run_ai_segment(WeekdayAvailabilitySchedulerActions, availability, segment_name=f"USER AVAILABILITY RUN {i}")
        result["user_availability"] = WeekdayAvailabilitySchedulerActions.get_user_list()
        result["user_macrocycles"] = run_ai_segment(MacrocycleActions, goal, segment_name=f"MACROCYCLES RUN {i}")
        result["user_mesocycles"] = run_schedule_segment(MesocycleActions, segment_name=f"MESOCYCLES RUN {i}")
        result["user_microcycles"] = run_segment(MicrocycleActions, segment_name=f"MICROCYCLES RUN {i}")
        result["user_planned_microcycle"] = run_schedule_segment(MicrocycleSchedulerActions, segment_name=f"MICROCYCLE PLAN RUN {i}")
        result["user_workout"] = run_schedule_segment(WorkoutActions, segment_name=f"WORKOUT EXERCISES RUN {i}")
        if verbose:
            print(f"\n========================== WORKOUT COMPLETED RUN {i} ==========================")
        result["user_workout"]["completed"] = WorkoutActions.complete_workout()
        results.append(result)
        if verbose:
            print(f"\n========================== FINISHED RUN {i} ==========================\n\n")

    return results

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


# Apply random performance metrics to all user exercises.
def populate_user_exercise(user_exercise):
    # Set the last performed to be a date to allow for performance decay
    days_since = randint(performance_decay_grace_period - 1, 
                         performance_decay_grace_period + 10)
    user_exercise.last_performed = date.today() - timedelta(days=days_since)

    # Set user exercise metrics to random performance values.
    new_density = randint(1, 100) / 100
    new_volume = randint(0, 40)

    # Add random weight to volume if weighted
    if user_exercise.exercises.is_weighted:
        new_volume *= randint(1, 100)
        user_exercise.one_rep_max = randint(10, 100)
    
    user_exercise.density = new_density
    user_exercise.volume = new_volume
    user_exercise.performance = new_density * new_volume
    db.session.commit()
    return user_exercise.to_dict()

# Set all of the user exercise performances to test performances and 1RM at a previous date for testing purposes.
@bp.route('/populate_user_exercises', methods=['POST'])
@login_required
def populate_user_exercises():
    user_exercises = current_user.exercises
    result = []
    for user_exercise in user_exercises:
        result.append(populate_user_exercise(user_exercise))
    return jsonify({"status": "success", "exercises": result}), 200


# Testing for the SQL to add and check training equipment.
@bp.route('/test_equipment_context', methods=['GET'])
def test_equipment_sql_context():
    results = {}
    
    user_question_1 = "Create a new user equipment for my new barbell that weighs 4 kilograms."
    result_1 = context_retriever_app.invoke({"question": user_question_1, "attempts": 0})
    results["result_1"] = {
        #"subjects": result_1["subjects"], 
        "results": result_1["query_result"]}
    #print("Subjects:", result_1["subjects"])
    print("Result:", result_1["query_result"])
    print("")
    
    user_question_2 = "Show me my training equipment."
    result_2 = context_retriever_app.invoke({"question": user_question_2, "attempts": 0})
    results["result_2"] = {
        #"subjects": result_2["subjects"], 
        "results": result_2["query_result"]}
    #print("Subjects:", result_2["subjects"])
    print("Result:", result_2["query_result"])
    print("")

    user_question_3 = "Show me if I am able to do weight lifting."
    result_3 = context_retriever_app.invoke({"question": user_question_3, "attempts": 0})
    results["result_3"] = {
        #"subjects": result_3["subjects"], 
        "results": result_3["query_result"]}
    #print("Subjects:", result_3["subjects"])
    print("Result:", result_3["query_result"])
    print("")
    

    user_question_4 = "Do I have the equipment available for me to do weight lifting?"
    result_4 = context_retriever_app.invoke({"question": user_question_4, "attempts": 0})
    results["result_4"] = {
        #"subjects": result_4["subjects"], 
        "results": result_4["query_result"]}
    #print("Subjects:", result_4["subjects"])
    print("Result:", result_4["query_result"])
    print("")

    user_question_5 = "Show me if I have the equipment available to do weight lifting."
    result_5 = context_retriever_app.invoke({"question": user_question_5, "attempts": 0})
    results["result_5"] = {
        #"subjects": result_5["subjects"], 
        "results": result_5["query_result"]}
    #print("Subjects:", result_5["subjects"])
    print("Result:", result_5["query_result"])
    print("")

    return results

'''
# Testing for constrain programming.
@bp.route('/test_cp_pulp_equipment', methods=['GET'])
def test_cp_pulp_equipment():
    results = {}
    
    result_1 = cp_pulp_equipment_test_main()
    print("\n\n\n\n\nRESULT")
    print(result_1["output"])
    #results["result_1"] = result_1

    return results'''