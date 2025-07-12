from flask import request, jsonify, Blueprint, abort
from flask_login import current_user, login_user, login_required, logout_user
from flask_cors import CORS

from app.models import Users
import psycopg2

from app import db

bp = Blueprint('auth', __name__)

# ----------------------------------------- Auth -----------------------------------------
@bp.route('/register', methods=['GET','POST'])
def register():
    if (request.method == 'POST' 
        and 'email' in request.form 
        and 'password' in request.form 
        and 'password_confirm' in request.form
        and 'first_name' in request.form
        and 'last_name' in request.form
        and 'age' in request.form
        and 'gender' in request.form
        and 'goal' in request.form):

        # Retreive and validate email
        email = request.form.get("email").strip().lower()
        
        if Users.query.filter_by(email=email).first():
            abort(400, description="Account with the email address of " + email + " already exists.")
        
        new_user = Users(
            first_name = request.form.get("first_name").strip().capitalize(), 
            last_name = request.form.get("last_name").strip().capitalize(),
            age = request.form.get("age"),
            gender = request.form.get("gender").strip().lower(),
            goal = request.form.get("goal"))

        # Validate and set email
        email_flag = new_user.set_email(email)
        if email_flag: 
            abort(400, description=email_flag)
        
        # Retrieve and validate password
        password_flag = new_user.set_password(
            request.form.get("password"), 
            request.form.get("password_confirm"))
        if password_flag: 
            abort(400, description=password_flag)
        
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"status": "success", "message": "New user added,"}), 200
        # return redirect(url_for('login'))
    elif request.method == 'POST':
        abort(400, description="Please fill out the form!")
    abort(400, description="GET is not valid for this route.")

@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        abort(400, description="You are already logged in!")
    if 'email' in request.form and 'password' in request.form:
        email = request.form.get("email")
        password = request.form.get("password")
        user = Users.query.filter_by(email=email).first()
        
        # Validate user existence and that password matches
        if user is None: 
            abort(404, description="Account with this email doesn't exist.")
        elif not user.check_password(password):
            abort(401, description="Password is incorrect.")
        else:
            login_user(user)
            return jsonify({"status": "success", "message": "Welcome back!"}), 200
    abort(400, description="Please fill out the form!")

@bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"status": "success", "message": "Logged out."}), 200

# Delete users based on id.
@bp.route('/delete_account', methods=['DELETE'])
@login_required
def delete_user():
    if ('password' in request.form):
        # Retreive and verify password
        password = request.form.get("password")
        if not password: 
            abort(400, description="Please enter current password to confirm change.")
        if not current_user.check_password(password):
            abort(401, description="Password is incorrect. Please try again.")
        user = Users.query.get(current_user.id)
        if user:
            db.session.delete(user)
            db.session.commit()
            logout_user
            return jsonify({"status": "success", "message": "Account deleted."}), 200
        abort(404, description="An account with this id has not been found.")
    abort(400, description="Please fill out the form!")