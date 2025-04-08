from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required
from flask_cors import CORS

from app.models import Users

from app import db, login_manager

bp = Blueprint('current_user', __name__)

from app.agents.workout_availability import create_workout_availability_extraction_graph

# ----------------------------------------- User Info -----------------------------------------
#Use Flask-Login to get current user
@bp.route('/', methods=['GET'])
@login_required
def get_current_user():
    if current_user.is_authenticated:
        return jsonify(current_user.to_dict()), 200
    return jsonify({"status": "error", "message": "User not authenticated"}), 401

@bp.route('/', methods=['PATCH'])
@login_required
def patch_current_user():
    if 'first_name' in request.form:
        first_name = request.form.get("first_name")
        current_user.first_name = first_name
    if 'last_name' in request.form:
        last_name = request.form.get("last_name")
        current_user.last_name = last_name
    if 'balance' in request.form:
        balance = float(request.form.get("balance"))
        current_user.balance = balance
    db.session.commit()
    return jsonify(current_user.to_dict()), 200


# Update account email.
@bp.route('/change_workout_length', methods=['PUT', 'PATCH'])
@login_required
def change_workout_length():
    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    
    if ('workout_length' not in data):
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400

    workout_app = create_workout_availability_extraction_graph()

    # Invoke with new workout_ and possible workout_ types.
    state = workout_app.invoke(
        {
            "new_availability": data.get("workout_length", ""), 
            "attempts": 0
        })
    
    current_user.workout_length = state["workout_availability"]
    db.session.commit()

    return jsonify({"status": "success", "message": "Availability changed to: " + str(state["workout_availability"])}), 200

# Update account email.
@bp.route('/change_email', methods=['PUT', 'PATCH'])
@login_required
def change_email():
    if ('new_email' in request.form 
        and 'password' in request.form):

        # Retreive and verify password
        password = request.form.get("password")
        if not password: 
            return jsonify({"status": "error", "message": "Please enter current password to confirm change."}), 400
        if not current_user.check_password(password):
            return jsonify({"status": "error", "message": "Password is incorrect. Please try again."}), 401

        # Retreive and validate new email
        new_email = request.form.get("new_email")
        if Users.query.filter_by(email=new_email).first():
            return jsonify({"status": "error", "message": "Account with the email address of " + new_email + " already exists."}), 400
        
        email_flag = current_user.set_email(new_email)
        if email_flag: 
            return jsonify({"status": "error", "message": email_flag}), 400
        
        # Change email
        current_user.email = new_email
        db.session.commit()
        return jsonify({"status": "success", "message": "Email changed to: " + new_email}), 200
    return jsonify({"status": "error", "message": "Please fill out the form!"}), 400

# Update account password.
@bp.route('/change_password', methods=['PUT','PATCH'])
@login_required
def change_password():
    if ('password' in request.form 
        and 'new_password' in request.form 
        and 'new_password_confirm' in request.form):

        # Retreive and verify old password
        password = request.form.get("password")
        if not password: 
            return jsonify({"status": "error", "message": "Please enter current password to confirm change."}), 400
        if not current_user.check_password(password):
            return jsonify({"status": "error", "message": "Password is incorrect. Please try again."}), 401
        
        # Retrieve and validate new password
        new_password = request.form.get("new_password")
        new_password_confirm = request.form.get("new_password_confirm")

        password_flag = current_user.set_password(new_password, new_password_confirm)
        if password_flag: 
            return jsonify({"status": "error", "message": password_flag}), 400
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Password successfully changed."}), 200
    return jsonify({"status": "error", "message": "Please fill out the form!"}), 400
