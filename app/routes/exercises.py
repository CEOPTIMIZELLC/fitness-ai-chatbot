import json

from flask import jsonify, Blueprint
from flask_login import current_user, login_required

from sqlalchemy.sql import func, distinct

from app import db
from app.models import Exercise_Library, Equipment_Library, User_Equipment

bp = Blueprint('exercises', __name__)

# ----------------------------------------- Exercises -----------------------------------------

# Retrieve exercises
@bp.route('/', methods=['GET'])
def get_exercise_list():
    exercises = Exercise_Library.query.all()
    result = []
    for exercise in exercises:
        result.append(exercise.to_dict())
    return jsonify({"status": "success", "exercises": result}), 200

# Show exercises based on id.
@bp.route('/<exercise_id>', methods=['GET'])
def read_exercise(exercise_id):
    exercise = db.session.get(Exercise_Library, exercise_id)
    if not exercise:
        return jsonify({"status": "error", "message": "Exercise " + exercise_id + " not found."}), 404
    return jsonify({"status": "success", "exercises": exercise.to_dict()}), 200


# Testing for the SQL to add and check training equipment.
@bp.route('/current', methods=['GET'])
@login_required
def get_exercises_user_can_perform():
    return "Done"
'''    # Subquery: Count distinct equipment types needed per exercise
    equipment_needed = (
        db.session.query(
            Exercise_Equipment.exercise_id,
            func.count(distinct(Exercise_Equipment.equipment_id)).label("required_count")
        )
        .group_by(Exercise_Equipment.exercise_id)
        .subquery()
    )

    # Subquery: Count distinct equipment types the user owns that are required for exercises
    equipment_owned = (
        db.session.query(
            Exercise_Equipment.exercise_id,
            func.count(distinct(User_Equipment.equipment_id)).label("owned_count")
        )
        .join(User_Equipment, Exercise_Equipment.equipment_id == User_Equipment.equipment_id)
        .filter(User_Equipment.user_id == current_user.id)
        .group_by(Exercise_Equipment.exercise_id)
        .subquery()
    )

    # Main Query: Select exercises where user owns all required equipment OR no equipment required
    exercises = (
        db.session.query(Exercise_Library)
        .outerjoin(equipment_needed, Exercise_Library.id == equipment_needed.c.exercise_id)
        .outerjoin(equipment_owned, Exercise_Library.id == equipment_owned.c.exercise_id)
        .filter(
            (equipment_needed.c.required_count == None) |  # No equipment required
            (equipment_needed.c.required_count == equipment_owned.c.owned_count)  # User owns all required equipment types
        )
        .distinct()
        .all()
    )
    result = []
    for exercise in exercises:
        result.append(exercise.to_dict())
    return jsonify({"status": "success", "exercises": result}), 200
'''