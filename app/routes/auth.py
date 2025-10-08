from logging_config import LogRoute

from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_user, login_required, logout_user
from flask_cors import CORS

from app.actions import enter_main_agent
from app.models import Users
import psycopg2

from app import db

bp = Blueprint('auth', __name__)

# ----------------------------------------- Auth -----------------------------------------
@bp.route('/register', methods=['GET','POST'])
def register():
    # Input is a json.
    data = request.get_json()
    if not data:
        abort(404, description="Invalid request")

    if (request.method == 'POST' 
        and 'email' in data 
        and 'password' in data 
        and 'password_confirm' in data
        and 'first_name' in data
        and 'last_name' in data
        and 'age' in data
        and 'gender' in data
        and 'goal' in data):

        # Retreive and validate email
        email = data.get("email").strip().lower()

        if Users.query.filter_by(email=email).first():
            abort(400, description="Account with the email address of " + email + " already exists.")
        
        new_user = Users(
            first_name = data.get("first_name").strip().capitalize(), 
            last_name = data.get("last_name").strip().capitalize(),
            age = data.get("age"),
            gender = data.get("gender").strip().lower(),
            goal = data.get("goal"))

        # Validate and set email
        email_flag = new_user.set_email(email)
        if email_flag: 
            abort(400, description=email_flag)
        
        # Retrieve and validate password
        password_flag = new_user.set_password(
            data.get("password"), 
            data.get("password_confirm"))
        if password_flag: 
            abort(400, description=password_flag)
        
        db.session.add(new_user)
        db.session.commit()

        LogRoute.verbose("Registered new user.")
        return jsonify({"status": "success", "response": "New user added,"}), 200
        # return redirect(url_for('login'))
    elif request.method == 'POST':
        abort(400, description="Please fill out the form!")
    abort(400, description="GET is not valid for this route.")

@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        abort(400, description="You are already logged in!")

    # Input is a json.
    data = request.get_json()
    if not data:
        abort(404, description="Invalid request")

    if 'email' in data and 'password' in data:
        email = data.get("email")
        password = data.get("password")
        user = Users.query.filter_by(email=email).first()
        
        # Validate user existence and that password matches
        if user is None: 
            abort(404, description="Account with this email doesn't exist.")
        elif not user.check_password(password):
            abort(401, description="Password is incorrect.")
        else:
            login_user(user)
            LogRoute.verbose("User logged in.")

            # Start new agent session.
            _ = enter_main_agent(current_user.id)

            return jsonify({"status": "success", "response": "Welcome back!"}), 200
    abort(400, description="Please fill out the form!")

@bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    LogRoute.verbose("User logged out.")
    return jsonify({"status": "success", "response": "Logged out."}), 200

# Delete users based on id.
@bp.route('/delete_account', methods=['DELETE'])
@login_required
def delete_user():
    # Input is a json.
    data = request.get_json()
    if not data:
        abort(404, description="Invalid request")

    if ('password' in data):
        # Retreive and verify password
        password = data.get("password")
        if not password: 
            abort(400, description="Please enter current password to confirm change.")
        if not current_user.check_password(password):
            abort(401, description="Password is incorrect. Please try again.")
        user = Users.query.get(current_user.id)
        if user:
            db.session.delete(user)
            db.session.commit()
            logout_user
            LogRoute.verbose("User deleted.")
            return jsonify({"status": "success", "response": "Account deleted."}), 200
        abort(404, description="An account with this id has not been found.")
    abort(400, description="Please fill out the form!")