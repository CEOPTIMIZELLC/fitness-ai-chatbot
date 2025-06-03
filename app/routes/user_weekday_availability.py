from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Weekday_Library, User_Weekday_Availability

from app.agents.weekday_availability import create_weekday_availability_extraction_graph

bp = Blueprint('user_weekday_availability', __name__)

# ----------------------------------------- User Weekday Availability -----------------------------------------
# Retrieve possible weekday types.
def retrieve_weekday_types():
    weekdays = (
        db.session.query(
            Weekday_Library.id,
            Weekday_Library.name
        )
        .all()
    )

    return [
        {
            "id": weekday.id, 
            "name": weekday.name.lower()
        } 
        for weekday in weekdays
    ]

# Retrieve current user's weekdays
@bp.route('/', methods=['GET'])
@login_required
def get_user_weekday_list():
    user_availability = current_user.availability
    result = []
    for weekday in user_availability:
        result.append(weekday.to_dict())
    return jsonify({"status": "success", "weekdays": result}), 200

# Change the current user's weekday.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def change_weekday_availability():
    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    
    if ('availability' not in data):
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400

    # There are only so many types a weekday can be classified as, with all of them being stored.
    weekday_types = retrieve_weekday_types()

    weekday_app = create_weekday_availability_extraction_graph()

    # Invoke with new weekday and possible weekday types.
    state = weekday_app.invoke(
        {
            "new_availability": data.get("availability", ""), 
            "weekday_types": weekday_types, 
            "attempts": 0
        })
    
    weekday_availability = state["weekday_availability"]
    # Update each availability entry to the database.
    for i in weekday_availability:
        db_entry = User_Weekday_Availability(user_id=current_user.id, 
                                             weekday_id=i["weekday_id"], 
                                             availability=i["availability"])
        db.session.merge(db_entry)
    db.session.commit()


    return jsonify({
        "new_availability": state["new_availability"]
    }), 200