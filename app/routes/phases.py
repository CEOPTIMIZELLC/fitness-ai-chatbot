from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Goal_Library, Goal_Phase_Requirements, Phase_Library, User_Mesocycles

bp = Blueprint('phases', __name__)

from app.agents.phases import Main as phase_main

# ----------------------------------------- Phases -----------------------------------------

# Retrieve phases
@bp.route('/', methods=['GET'])
def get_phase_list():
    phases = Phase_Library.query.all()
    result = []
    for phase in phases:
        result.append(phase.to_dict())
    return jsonify({"status": "success", "phases": result}), 200

# Show phases based on id.
@bp.route('/<phase_id>', methods=['GET'])
def read_phase(phase_id):
    phase = Phase_Library.query.filter_by(id=phase_id).first()
    if not phase:
        return jsonify({"status": "error", "message": "Phase " + phase_id + " not found."}), 404
    return jsonify(phase.to_dict()), 200


# Testing for the parameter programming for mesocycle labeling.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def mesocycle_phases():

    config = {
        "parameters": {},
        "constraints": {}
    }

    user_macro = current_user.current_macrocycle

    config["parameters"]["macrocycle_weeks"] = 26
    config["parameters"]["goal_type"] = user_macro.goal_id

    possible_phases = (
        db.session.query(
            Phase_Library.id,
            Phase_Library.name,
            Phase_Library.phase_duration_minimum_in_weeks,
            Phase_Library.phase_duration_maximum_in_weeks,
            Goal_Phase_Requirements.required_phase,
            Goal_Phase_Requirements.is_goal_phase,
        )
        .join(Goal_Phase_Requirements, Goal_Phase_Requirements.phase_id == Phase_Library.id)
        .join(Goal_Library, Goal_Library.id == Goal_Phase_Requirements.goal_id)
        .filter(
            Goal_Library.id == user_macro.goal_id
        )
        .all()
    )

    possible_phases_dict = {}

    for possible_phase in possible_phases:
        possible_phases_dict[possible_phase.name.lower()] = {
            "id": possible_phase.id,
            "phase_duration_minimum_in_weeks": possible_phase.phase_duration_minimum_in_weeks,
            "phase_duration_maximum_in_weeks": possible_phase.phase_duration_maximum_in_weeks,
            "required_phase": True if possible_phase.required_phase == "required" else False,
            #"required_phase": possible_phase.required_phase,
            "is_goal_phase": possible_phase.is_goal_phase,
        }
    
    #config["possible_phases"] = possible_phases
    config["parameters"]["possible_phases"] = possible_phases_dict

    result = phase_main(parameter_input=config)

    print(result["formatted"])

    phases_output = result["output"]

    # Convert output to form that may be stored.

    from datetime import timedelta
    user_phases = []
    order = 1
    mesocycle_start_date = user_macro.start_date
    for phase in phases_output:
        new_phase = User_Mesocycles(
            macrocycle_id = user_macro.id,
            phase_id = phase["id"],
            order = order,
            start_date = mesocycle_start_date,
            end_date = mesocycle_start_date + timedelta(weeks=phase["duration"])
        )
        user_phases.append(new_phase)

        # Set startdate of next phase to be at the end of the current one.
        mesocycle_start_date +=timedelta(weeks=phase["duration"])
        order += 1
    
    db.session.add_all(user_phases)
    db.session.commit()

    return result


# Testing for the parameter programming for mesocycle labeling.
@bp.route('/phase_classification_test', methods=['GET'])
def phase_classification_test():
    import json

    test_results = []

    config = {
        "parameters": {},
        "constraints": {}
    }
    config["parameters"]["macrocycle_weeks"] = 26

    # Retrieve all possible goals.
    #goals = (db.session.query(Goal_Library.id).group_by(Goal_Library.id).all())
    goals = (
        db.session.query(Goal_Library.id)
        .join(Goal_Phase_Requirements, Goal_Library.id == Goal_Phase_Requirements.goal_id)  # Adjust column names as necessary
        .group_by(Goal_Library.id)
        .all()
    )


    # Test for all goals that exist.
    for goal in goals:
        possible_phases = (
            db.session.query(
                Phase_Library.id,
                Phase_Library.name,
                Phase_Library.phase_duration_minimum_in_weeks,
                Phase_Library.phase_duration_maximum_in_weeks,
                Goal_Phase_Requirements.required_phase,
                Goal_Phase_Requirements.is_goal_phase,
            )
            .join(Goal_Phase_Requirements, Goal_Phase_Requirements.phase_id == Phase_Library.id)
            .join(Goal_Library, Goal_Library.id == Goal_Phase_Requirements.goal_id)
            .filter(
                Goal_Library.id == int(goal.id)
            )
            .all()
        )

        possible_phases_dict = {}

        for possible_phase in possible_phases:
            possible_phases_dict[possible_phase.name.lower()] = {
                "phase_duration_minimum_in_weeks": possible_phase.phase_duration_minimum_in_weeks,
                "phase_duration_maximum_in_weeks": possible_phase.phase_duration_maximum_in_weeks,
                "required_phase": True if possible_phase.required_phase == "required" else False,
                #"required_phase": possible_phase.required_phase,
                "is_goal_phase": possible_phase.is_goal_phase,
            }
        
        config["parameters"]["possible_phases"] = possible_phases_dict

        result = phase_main(parameter_input=config)
        for x, y in result.items():
            print(x, ":", y)
        test_results.append({
            "macrocycle_weeks": config["parameters"]["macrocycle_weeks"], 
            "goal_id": goal.id,
            "result": result
        })
        print("----------------------")

    return test_results
