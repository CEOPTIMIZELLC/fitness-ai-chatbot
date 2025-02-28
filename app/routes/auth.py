from flask import request, jsonify, Blueprint
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
            return jsonify({"status": "error", "message": "Account with the email address of " + email + " already exists."}), 400
        
        new_user = Users(
            first_name = request.form.get("first_name").strip().capitalize(), 
            last_name = request.form.get("last_name").strip().capitalize(),
            age = request.form.get("age"),
            gender = request.form.get("gender").strip().lower(),
            goal = request.form.get("goal"))

        # Validate and set email
        email_flag = new_user.set_email(email)
        if email_flag: 
            return jsonify({"status": "error", "message": email_flag}), 400
        
        # Retrieve and validate password
        password_flag = new_user.set_password(
            request.form.get("password"), 
            request.form.get("password_confirm"))
        if password_flag: 
            return jsonify({"status": "error", "message": password_flag}), 400
        
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"status": "success", "message": "New user added,"}), 200
        # return redirect(url_for('login'))
    elif request.method == 'POST':
        return jsonify({"status": "error", "message": "Please fill out the form!"}), 400
    return jsonify({"status": "error", "message": "GET is not valid for this route."}), 400

@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({"status": "error", "message": "You are already logged in!"}), 400
    if 'email' in request.form and 'password' in request.form:
        email = request.form.get("email")
        password = request.form.get("password")
        user = Users.query.filter_by(email=email).first()
        
        # Validate user existence and that password matches
        if user is None: 
            return jsonify({"status": "error", "message": "Account with this email doesn't exist."}), 400
        elif not user.check_password(password):
            return jsonify({"status": "error", "message": "Password is incorrect."}), 400
        else:
            login_user(user)
            return jsonify({"status": "success", "message": "Welcome back!"}), 200
    return jsonify({"status": "error", "message": "Please fill out the form!"}), 400

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
            return jsonify({"status": "error", "message": "Please enter current password to confirm change."}), 400
        if not current_user.check_password(password):
            return jsonify({"status": "error", "message": "Password is incorrect. Please try again."}), 401
        user = Users.query.get(current_user.id)
        if user:
            db.session.delete(user)
            db.session.commit()
            logout_user
            return jsonify({"status": "success", "message": "Account deleted."}), 200
        return jsonify({"status": "error", "message": "An account with this id has not been found."}), 400
    return jsonify({"status": "error", "message": "Please fill out the form!"}), 400