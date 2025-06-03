from flask import request, jsonify, Blueprint
from flask_login import current_user, login_required
from flask_cors import CORS

from app.models import Users

from app import db, login_manager

from app.agents.workout_availability import create_workout_availability_extraction_graph

bp = Blueprint('current_user', __name__)

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
    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    if 'first_name' in data:
        first_name = data.get("first_name")
        current_user.first_name = first_name
    if 'last_name' in data:
        last_name = data.get("last_name")
        current_user.last_name = last_name
    if 'balance' in data:
        balance = float(data.get("balance"))
        current_user.balance = balance
    db.session.commit()
    return jsonify(current_user.to_dict()), 200

# Update account email.
@bp.route('/change_email', methods=['PUT', 'PATCH'])
@login_required
def change_email():
    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    
    if ('new_email' not in data) or ('password' not in data):
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400

    # Retreive and verify password
    password = data.get("password")
    if not password: 
        return jsonify({"status": "error", "message": "Please enter current password to confirm change."}), 400
    if not current_user.check_password(password):
        return jsonify({"status": "error", "message": "Password is incorrect. Please try again."}), 401

    # Retreive and validate new email
    new_email = data.get("new_email")
    if Users.query.filter_by(email=new_email).first():
        return jsonify({"status": "error", "message": "Account with the email address of " + new_email + " already exists."}), 400
    
    email_flag = current_user.set_email(new_email)
    if email_flag: 
        return jsonify({"status": "error", "message": email_flag}), 400
    
    # Change email
    current_user.email = new_email
    db.session.commit()
    return jsonify({"status": "success", "message": "Email changed to: " + new_email}), 200

# Update account password.
@bp.route('/change_password', methods=['PUT','PATCH'])
@login_required
def change_password():
    # Input is a json.
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    
    if ('new_password' not in data) or ('new_password_confirm' not in data) or ('password' not in data):
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400
    # Retreive and verify old password
    password = data.get("password")
    if not password: 
        return jsonify({"status": "error", "message": "Please enter current password to confirm change."}), 400
    if not current_user.check_password(password):
        return jsonify({"status": "error", "message": "Password is incorrect. Please try again."}), 401
    
    # Retrieve and validate new password
    new_password = data.get("new_password")
    new_password_confirm = data.get("new_password_confirm")

    password_flag = current_user.set_password(new_password, new_password_confirm)
    if password_flag: 
        return jsonify({"status": "error", "message": password_flag}), 400
    
    db.session.commit()
    return jsonify({"status": "success", "message": "Password successfully changed."}), 200
