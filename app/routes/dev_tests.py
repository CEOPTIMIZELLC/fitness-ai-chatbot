from logging_config import LogRoute
from random import randint
from datetime import timedelta, date
from flask import request, jsonify, Blueprint, abort

from flask_login import current_user, login_required

from config import ExercisePerformanceDecayConfig
from app import db
from app.utils.sql import sql_app
from app.utils.table_context_parser import context_retriever_app

from app.main_sub_agents.user_macrocycles import create_goal_agent
from app.main_sub_agents.user_mesocycles import create_mesocycle_agent
from app.main_sub_agents.user_microcycles import create_microcycle_agent
from app.main_sub_agents.user_workout_days import create_microcycle_scheduler_agent
from app.main_sub_agents.user_workout_exercises import create_workout_agent
from app.main_sub_agents.user_workout_completion import create_workout_completion_agent
from app.main_sub_agents.user_weekdays_availability import create_availability_agent

from app.utils.item_to_string import recursively_change_dict_timedeltas

bp = Blueprint('dev_tests', __name__)

# ----------------------------------------- Dev Tests -----------------------------------------

# The various templates used throughout the pipeline.
state_templates = {
    "alter": {
        "is_requested": True, 
        "is_alter": True, 
        "is_read": True, 
        "read_plural": False, 
        "read_current": False, 
        "detail": "Perform", 
    }, 
    "current_list": {
        "is_requested": True, 
        "is_alter": False, 
        "is_read": False, 
        "read_plural": False, 
        "read_current": True, 
        "detail": "Retrieve", 
    }, 
}

# Adds the keys necessary for a sub agent to the final state.
def sub_agent_state_constructor(state, sub_agent_name, state_template, message=None):
    if not message:
        message = f"{state_template["detail"]} {sub_agent_name}."

    state[f"{sub_agent_name}_is_requested"] = state_template["is_requested"]
    state[f"{sub_agent_name}_is_alter"] = state_template["is_alter"]
    state[f"{sub_agent_name}_read_plural"] = state_template["read_plural"]
    state[f"{sub_agent_name}_read_current"] = state_template["read_current"]
    state[f"{sub_agent_name}_detail"] = message
    return state

# Constructs the complete state used by all of the sub agents.
def agent_state_constructor(state_template, data={}, alter_old=False):
    state = {"user_id": current_user.id}
    state = sub_agent_state_constructor(state, "availability", state_template, data.get("availability", ""))
    state = sub_agent_state_constructor(state, "macrocycle", state_template, data.get("goal", ""))
    state["macrocycle_alter_old"] = alter_old
    state = sub_agent_state_constructor(state, "mesocycle", state_template)
    state = sub_agent_state_constructor(state, "microcycle", state_template)
    state = sub_agent_state_constructor(state, "phase_component", state_template)
    state = sub_agent_state_constructor(state, "workout_schedule", state_template)
    state = sub_agent_state_constructor(state, "workout_completion", state_template)
    return state

# Initalizes the sub agents.
def initialize_sub_agents():
    sub_agents = {}
    sub_agents["availability"] = create_availability_agent()
    sub_agents["goal"] = create_goal_agent()
    sub_agents["mesocycle"] = create_mesocycle_agent()
    sub_agents["microcycle"] = create_microcycle_agent()
    sub_agents["microcycle_scheduler"] = create_microcycle_scheduler_agent()
    sub_agents["workout"] = create_workout_agent()
    sub_agents["workout_completion"] = create_workout_completion_agent()
    return sub_agents

def run_schedule_segment(state, subagent, segment_name=None):
    if segment_name:
        LogRoute.verbose(f"\n========================== {segment_name} ==========================")
    result = subagent.invoke(state)
    return result

# Runs a single iteration of the pipeline.
def run_sub_agents_singular(i, state, sub_agents):
    result = {}
    result["user_availability"] = run_schedule_segment(state, sub_agents["availability"], segment_name=f"AVAILABILITY RUN {i}")
    result["user_macrocycles"] = run_schedule_segment(state, sub_agents["goal"], segment_name=f"MACROCYCLES RUN {i}")
    result["user_mesocycles"] = run_schedule_segment(state, sub_agents["mesocycle"], segment_name=f"MESOCYCLES RUN {i}")
    result["user_microcycles"] = run_schedule_segment(state, sub_agents["microcycle"], segment_name=f"MICROCYCLES RUN {i}")
    result["user_planned_microcycle"] = run_schedule_segment(state, sub_agents["microcycle_scheduler"], segment_name=f"MICROCYCLE PLAN RUN {i}")
    result["user_workout"] = run_schedule_segment(state, sub_agents["workout"], segment_name=f"WORKOUT EXERCISES RUN {i}")
    result["user_workout_completion"] = run_schedule_segment(state, sub_agents["workout_completion"], segment_name=f"WORKOUT COMPLETED RUN {i}")

    # Correct time delta for serializing for JSON output.
    result = recursively_change_dict_timedeltas(result)
    return result

# Runs all of the sub agents for the specified number of runs.
def run_sub_agents(state, sub_agents, runs=1):
    results = []
    for i in range(1, runs+1):
        result = run_sub_agents_singular(i, state, sub_agents)
        results.append(result)
        LogRoute.verbose(f"\n========================== FINISHED RUN {i} ==========================\n\n")

    return results


# Quick check of the entire pipeline
@bp.route('/pipeline', methods=['GET'])
@login_required
def check_pipeline():
    state = agent_state_constructor(state_templates["current_list"])
    sub_agents = initialize_sub_agents()
    results = run_sub_agents(state, sub_agents)
    return results

# Quick test of the entire pipeline
@bp.route('/pipeline', methods=['POST', 'PATCH'])
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

    # Determine if a new macrocycle should be made instead of changing the current one.
    if (request.method == 'PATCH'):
        alter_old = True
    else:
        alter_old = False

    state = agent_state_constructor(state_templates["alter"], data, alter_old)
    sub_agents = initialize_sub_agents()
    runs = data.get("runs", 1)
    results = run_sub_agents(state, sub_agents, runs)
    return results

# Testing for the SQL to add and check training equipment.
@bp.route('/test_equipment_sql', methods=['GET'])
def test_equipment_sql():
    results = {}
    user_question_1 = "Create a new user equipment for my new barbell that weighs 4 kilograms."
    result_1 = sql_app.invoke({"question": user_question_1, "attempts": 0})
    results["result_1"] = result_1["query_result"]
    LogRoute.verbose("Result:", result_1["query_result"])
    LogRoute.verbose("")
    
    user_question_2 = "Create a new user equipment for my new treadmill that is 20 centimeters long."
    result_2 = sql_app.invoke({"question": user_question_2, "attempts": 0})
    results["result_2"] = result_2["query_result"]
    LogRoute.verbose("Result:", result_2["query_result"])
    LogRoute.verbose("")

    user_question_3 = "Show me my training equipment."
    result_3 = sql_app.invoke({"question": user_question_3, "attempts": 0})
    results["result_3"] = result_3["query_result"]
    LogRoute.verbose("Result:", result_3["query_result"])
    LogRoute.verbose("")

    user_question_4 = "Create a new user training equipment for my new treadmill."
    result_4 = sql_app.invoke({"question": user_question_4, "attempts": 0})
    results["result_4"] = result_4["query_result"]
    LogRoute.verbose("Result:", result_4["query_result"])
    LogRoute.verbose("")

    user_question_5 = "Show me my training equipment."
    result_5 = sql_app.invoke({"question": user_question_5, "attempts": 0})
    results["result_5"] = result_5["query_result"]
    LogRoute.verbose("Result:", result_5["query_result"])
    LogRoute.verbose("")

    return results


# Apply random performance metrics to all user exercises.
def populate_user_exercise(user_exercise):
    # Set the last performed to be a date to allow for performance decay
    days_since = randint(ExercisePerformanceDecayConfig.grace_period - 1, 
                         ExercisePerformanceDecayConfig.grace_period + 10)
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
    #LogRoute.verbose("Subjects:", result_1["subjects"])
    LogRoute.verbose("Result:", result_1["query_result"])
    LogRoute.verbose("")
    
    user_question_2 = "Show me my training equipment."
    result_2 = context_retriever_app.invoke({"question": user_question_2, "attempts": 0})
    results["result_2"] = {
        #"subjects": result_2["subjects"], 
        "results": result_2["query_result"]}
    #LogRoute.verbose("Subjects:", result_2["subjects"])
    LogRoute.verbose("Result:", result_2["query_result"])
    LogRoute.verbose("")

    user_question_3 = "Show me if I am able to do weight lifting."
    result_3 = context_retriever_app.invoke({"question": user_question_3, "attempts": 0})
    results["result_3"] = {
        #"subjects": result_3["subjects"], 
        "results": result_3["query_result"]}
    #LogRoute.verbose("Subjects:", result_3["subjects"])
    LogRoute.verbose("Result:", result_3["query_result"])
    LogRoute.verbose("")
    

    user_question_4 = "Do I have the equipment available for me to do weight lifting?"
    result_4 = context_retriever_app.invoke({"question": user_question_4, "attempts": 0})
    results["result_4"] = {
        #"subjects": result_4["subjects"], 
        "results": result_4["query_result"]}
    #LogRoute.verbose("Subjects:", result_4["subjects"])
    LogRoute.verbose("Result:", result_4["query_result"])
    LogRoute.verbose("")

    user_question_5 = "Show me if I have the equipment available to do weight lifting."
    result_5 = context_retriever_app.invoke({"question": user_question_5, "attempts": 0})
    results["result_5"] = {
        #"subjects": result_5["subjects"], 
        "results": result_5["query_result"]}
    #LogRoute.verbose("Subjects:", result_5["subjects"])
    LogRoute.verbose("Result:", result_5["query_result"])
    LogRoute.verbose("")

    return results

'''
# Testing for constrain programming.
@bp.route('/test_cp_pulp_equipment', methods=['GET'])
def test_cp_pulp_equipment():
    results = {}
    
    result_1 = cp_pulp_equipment_test_main()
    LogRoute.verbose("\n\n\n\n\nRESULT")
    LogRoute.verbose(result_1["output"])
    #results["result_1"] = result_1

    return results'''