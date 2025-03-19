from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Goal_Library, Goal_Phase_Requirements, Phase_Library, Phase_Component_Library, Phase_Components_Component_Library, Phase_Component_Bodyparts, User_Workout_Days, User_Workout_Components, User_Microcycles, User_Mesocycles, User_Macrocycles
from datetime import datetime, timedelta

bp = Blueprint('user_workout_days', __name__)

from app.agents.phase_components import Main as phase_component_main
from app.helper_functions.common_table_queries import current_macrocycle, current_microcycle, current_workout_day

# ----------------------------------------- Phase_Components -----------------------------------------

def delete_old_user_workout_days(microcycle_id):
    db.session.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
    print("Successfully deleted")

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_possible_phase_components(phase_id):
    # Retrieve all possible phase components that can be selected.
    possible_phase_components = (
        Phase_Component_Library.query
        .join(Phase_Library)
        .filter(Phase_Library.id == phase_id)
        .order_by(Phase_Component_Library.id.asc())
        .all()
    )
    return possible_phase_components

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_phase_component_bodyparts(phase_id):
    # Retrieve all possible phase components that can be selected.
    possible_phase_component_bodyparts = (
        Phase_Component_Bodyparts.query
        .filter(Phase_Component_Bodyparts.phase_id == phase_id)
        .order_by(Phase_Component_Bodyparts.id.asc())
        .all()
    )
    return possible_phase_component_bodyparts    

def construct_phase_component_list(possible_phase_components, possible_phase_component_bodyparts):
    possible_phase_components_list = []

    # Convert the query into a list of dictionaries.
    for possible_phase_component in possible_phase_components:
        # If the phase component is resistance, append it multiple times.
        if possible_phase_component.component_id == 6:
            for possible_phase_component_bodypart in possible_phase_component_bodyparts:
                possible_phase_components_list.append(
                    possible_phase_component.to_dict() | {
                    "bodypart_id": possible_phase_component_bodypart.bodypart_id, 
                    "bodypart": possible_phase_component_bodypart.bodyparts.name})
        # Append only once for full body if any other phase component.
        else:
            possible_phase_components_list.append(possible_phase_component.to_dict() | {"bodypart_id": 1, "bodypart": "total_body"})
    
    return possible_phase_components_list

# Given a start date and a duration, convert into a list of weekdays and create a corresponding workout day entry.
def duration_to_weekdays(dur, start_date, microcycle_id):
    microcycle_weekdays = []
    user_workdays = []

    weekday_number = start_date.weekday()

    # Loop through the number of iterations
    for i in range(dur):
        # Calculate the current number using modulo to handle the circular nature
        microcycle_weekdays.append((weekday_number + i) % 7)

        new_workday = User_Workout_Days(
            microcycle_id = microcycle_id,
            order = i+1,
            date = (start_date + timedelta(days=i))
        )
        user_workdays.append(new_workday)
    
    return microcycle_weekdays, user_workdays


def agent_output_to_sqlalchemy_model(phase_components_output, user_workdays):
    for phase_component in phase_components_output:
        # Create a new component entry.
        new_component = User_Workout_Components(
            phase_component_id = phase_component["phase_component_id"],
            bodypart_id = phase_component["bodypart_id"],
            order = 0,
            rep = phase_component["reps_var"],
            sets = phase_component["sets_var"],
            intensity = 0,
            rest = phase_component["rest_var"],
            exercises_per_bodypart = phase_component["bodypart_var"]
        )

        # Append the component to its corresponding workday.
        user_workdays[phase_component["workday_index"]].workout_components.append(new_component)
    return user_workdays



# Retrieve phase components
@bp.route('/', methods=['GET'])
@login_required
def get_user_workout_days():
    user_workout_days = User_Workout_Days.query.join(User_Microcycles).join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=current_user.id).all()
    result = []
    for user_workout_day in user_workout_days:
        result.append(user_workout_day.to_dict())
    return jsonify({"status": "success", "phase_components": result}), 200

# Retrieve phase components
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_workout_days():
    result = []
    user_microcycle = current_microcycle(current_user.id)
    user_workout_days = user_microcycle.workout_days
    for user_workout_day in user_workout_days:
        result.append(user_workout_day.to_dict())
    return jsonify({"status": "success", "phase_components": result}), 200

# Retrieve user's current phase component
@bp.route('/current', methods=['GET'])
@login_required
def get_user_current_workout_day():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active phase component found."}), 404
    return jsonify({"status": "success", "phase_component": user_workout_day.to_dict()}), 200


# Gives four mirocycles for microcycle.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def workout_day_initializer():

    config = {
        "parameters": {},
        "constraints": {}
    }

    user_microcycle = current_microcycle(current_user.id)

    delete_old_user_workout_days(user_microcycle.id)

    microcycle_weekdays, user_workdays = duration_to_weekdays(user_microcycle.duration.days, user_microcycle.start_date, user_microcycle.id)

    config["parameters"]["microcycle_weekdays"] = microcycle_weekdays

    # Retrieve all possible phase component body parts.
    possible_phase_component_bodyparts = retrieve_phase_component_bodyparts(user_microcycle.mesocycles.phase_id)

    # Retrieve all possible phase components that can be selected for the phase id.
    possible_phase_components = retrieve_possible_phase_components(user_microcycle.mesocycles.phase_id)
    possible_phase_components_list = construct_phase_component_list(possible_phase_components, possible_phase_component_bodyparts)

    config["parameters"]["phase_components"] = possible_phase_components_list

    result = phase_component_main(parameter_input=config)
    print(result["formatted"])

    user_workdays = agent_output_to_sqlalchemy_model(result["output"], user_workdays)

    db.session.add_all(user_workdays)
    db.session.commit()

    return result



# Testing for the parameter programming for mesocycle labeling.
@bp.route('/test', methods=['GET', 'POST'])
def phase_component_classification_test():
    test_results = []

    config = {
        "parameters": {},
        "constraints": {}
    }
    config["parameters"] = {
        "weekday_availability": [
            {"id": 0, "name": "Monday", "availability": 6 * 60 * 60},
            {"id": 1, "name": "Tuesday", "availability": 3 * 60 * 60},
            {"id": 2, "name": "Wednesday", "availability": 2 * 60 * 60},
            {"id": 3, "name": "Thursday", "availability": 35 * 60},
            {"id": 4, "name": "Friday", "availability": 0 * 60 * 60},
            {"id": 5, "name": "Saturday", "availability": 2 * 60 * 60},
            {"id": 6, "name": "Sunday", "availability": 0 * 60 * 60},
        ],
        "microcycle_weekdays": [0, 1, 2, 3, 4, 5, 6],
        "workout_length": 50 * 60,
        "phase_components": []
    }

    # Retrieve all possible phases.
    phases = (
        db.session.query(Phase_Library.id)
        .group_by(Phase_Library.id)
        .order_by(Phase_Library.id.asc())
        .all()
    )

    for phase in phases:
        # Retrieve all possible phase component body parts.
        possible_phase_component_bodyparts = retrieve_phase_component_bodyparts(phase.id)

        # Retrieve all possible phase components that can be selected for the phase id.
        possible_phase_components = retrieve_possible_phase_components(phase.id)
        possible_phase_components_list = construct_phase_component_list(possible_phase_components, possible_phase_component_bodyparts)

        config["parameters"]["phase_components"] = possible_phase_components_list

        result = phase_component_main(parameter_input=config)
        print(str(phase.id))
        print(result["formatted"])
        test_results.append({
            "phase_components": config["parameters"]["phase_components"], 
            "phase_id": phase.id,
            "result": result
        })
        print("----------------------")

    return test_results