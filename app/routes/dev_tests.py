from random import randrange
from flask import request, jsonify, Blueprint

from flask_login import current_user, login_required

from app.utils.sql import sql_app
from app.utils.table_context_parser import context_retriever_app

bp = Blueprint('dev_tests', __name__)

# ----------------------------------------- Dev Tests -----------------------------------------

def retrieve_output_from_endpoint(result, key):
    success_check = (result[1] == 200)
    output = result[0].get_json()
    if success_check:
        output_value = output[key]
        if not isinstance(output_value, dict):
            return output_value, success_check
        return output_value.get("output", output_value), success_check
    else:
        return output, success_check

def run_segment(result, segment_method, result_key, output_key, segment_name=None):
    if segment_name:
        print(f"\n========================== {segment_name} ==========================")
    result_temp = segment_method()
    result[result_key], success_check = retrieve_output_from_endpoint(result_temp, output_key)
    return success_check

# Quick check of the entire pipeline
@bp.route('/pipeline', methods=['GET'])
@login_required
def check_pipeline():
    from app.routes.user_weekday_availability import get_user_weekday_list
    from app.routes.user_macrocycles import read_user_current_macrocycle
    from app.routes.user_mesocycles import get_user_current_mesocycles_list
    from app.routes.user_microcycles import get_user_current_microcycles_list
    from app.routes.user_workout_days import get_user_current_workout_days_list
    from app.routes.user_workout_exercises import get_user_current_exercises_list
    from app.routes.user_exercises import get_user_current_exercise_list

    result = {}
    run_segment(result, get_user_weekday_list, "user_availability", "weekdays")
    run_segment(result, read_user_current_macrocycle, "user_macrocycles", "macrocycles")
    run_segment(result, get_user_current_mesocycles_list, "user_mesocycles", "mesocycles")
    run_segment(result, get_user_current_microcycles_list, "user_microcycles", "microcycles")
    run_segment(result, get_user_current_workout_days_list, "user_workout_days", "phase_components")
    run_segment(result, get_user_current_exercises_list, "user_workout_exercises", "exercises")
    run_segment(result, get_user_current_exercise_list, "user_exercises", "user_exercises")
    return result


def failed_run(result, results, i=0):
    results.append(result)
    print(f"\n========================== FAILED RUN {i} ==========================\n\n")
    return results

def run_availability_segment(result, segment_method, segment_method_2, result_key, output_key, segment_name):
    print(f"\n========================== {segment_name} ==========================")
    segment_method()
    return run_segment(result, segment_method_2, result_key, output_key)



# Quick test of the entire pipeline
@bp.route('/pipeline', methods=['POST'])
@login_required
def run_pipeline():
    from app.routes.user_weekday_availability import change_weekday_availability, get_user_weekday_list
    from app.routes.user_macrocycles import change_macrocycle
    from app.routes.user_mesocycles import mesocycle_phases
    from app.routes.user_microcycles import microcycle_initializer
    from app.routes.user_workout_days import workout_day_initializer
    from app.routes.user_workout_exercises import exercise_initializer, complete_workout

    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    runs = data.get("runs", 1)
    results = []
    for i in range(1, runs+1):
        result = {}
        if not run_availability_segment(result, change_weekday_availability, get_user_weekday_list, "user_availability", "weekdays", f"USER AVAILABILITY RUN {i}"):
            return failed_run(result, results, i)
        if not run_segment(result, change_macrocycle, "user_macrocycles", "macrocycles", f"MACROCYCLES RUN {i}"):
            return failed_run(result, results, i)
        if not run_segment(result, mesocycle_phases, "user_mesocycles", "mesocycles", f"MESOCYCLES RUN {i}"):
            return failed_run(result, results, i)
        if not run_segment(result, microcycle_initializer, "user_microcycles", "microcycles", f"MICROCYCLES RUN {i}"):
            return failed_run(result, results, i)
        if not run_segment(result, workout_day_initializer, "user_workout_days", "workdays", f"WORKOUT DAYS RUN {i}"):
            return failed_run(result, results, i)
        if not run_segment(result, exercise_initializer, "user_workout_exercises", "exercises", f"EXERCISES RUN {i}"):
            return failed_run(result, results, i)
        if not run_segment(result, complete_workout, "user_exercises", "user_exercises", f"WORKOUT COMPLETED RUN {i}"):
            return failed_run(result, results, i)
        results.append(result)
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