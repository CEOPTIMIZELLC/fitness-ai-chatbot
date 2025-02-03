from app import db, bcrypt, login_manager
from flask_login import UserMixin
from app import user_validate

from sqlalchemy.dialects.postgresql import TEXT, JSONB

class Users(db.Model, UserMixin):
    __tablename__ = "users"

    # Fields 
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String, nullable=False)

    goal = db.Column(
        TEXT, 
        nullable=False, 
        comment='General fitness goal (e.g., Strength, Endurance)')
    
    start_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp(), 
        nullable=False)

    def set_email(self, email):
        # Make sure that email is in a valid format.
        email, email_valid = user_validate.is_email_valid(email)
        if not email_valid: 
            return email
        self.email = email
        return None

    def set_password(self, password, password_confirm):
        # Make sure that both passwords match.
        if not user_validate.do_passwords_match(password, password_confirm):
            return "Passwords should match!"
        
        # Make sure that the password is in a valid format.
        password_flag = user_validate.is_password_valid(password)
        if password_flag: 
            return password_flag
        
        # If input password has passed all tests, set the password.
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        return None
    
    # Make sure password matches
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    # Relationships
    injuries = db.relationship(
        "User_Injuries",
        back_populates = "users",
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "gender": self.gender,
            "goal": self.goal,
            "start_date": self.start_date
    
        }

# User loader for flask-login
@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)


# The table of injuries that a user currently or previously has.
class User_Injuries(db.Model):
    # Fields
    __tablename__ = "user_injuries"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    injury_id = db.Column(db.Integer, db.ForeignKey("injury_library.id"), nullable=False)
    
    severity = db.Column(
        db.String(50),
        nullable=False,
        comment='E.g., Mild, Moderate, Severe')
    
    affected_muscle_groups = db.Column(
        JSONB,
        nullable=False,
        comment='E.g., {"lower_body": true, "upper_body": false}')
    
    start_date = db.Column(db.Date, nullable=False)
    projected_end_date = db.Column(db.Date, nullable=False)

    actual_end_date = db.Column(
        db.Date,
        nullable=False,
        comment='Filled in when the client fully recovers')
    
    current_status = db.Column(
        db.String(50),
        nullable=False,
        comment='E.g., Recovering, Cleared, Worsened')
    
    status_updated_at = db.Column(
        db.Date,
        nullable=False,
        comment='When the last status update was made')
    
    # Relationships
    users = db.relationship(
        "Users",
        back_populates = "injuries")
    
    injuries = db.relationship(
        "Injury_Library",
        back_populates = "users")
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "injury_name": self.injuries.name,
        }

