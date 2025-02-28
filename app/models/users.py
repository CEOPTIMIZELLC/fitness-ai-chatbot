from app import db, bcrypt, login_manager
from flask_login import UserMixin
from app import user_validate

from sqlalchemy.dialects.postgresql import TEXT, JSONB
from sqlalchemy.ext.hybrid import hybrid_property

from .user_macrocycles import User_Macrocycles

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
        nullable=True, 
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
    
    # Current Macrocycle Goal ID
    @hybrid_property
    def current_macrocycle(self):
        from datetime import date
        today = date.today()
        active_macrocycle = (
            User_Macrocycles.query.filter(
                User_Macrocycles.start_date <= today, 
                User_Macrocycles.end_date >= today
            ).order_by(User_Macrocycles.id.desc()
            ).first())
        return active_macrocycle
    
    # Relationships
    equipment = db.relationship(
        "User_Equipment",
        back_populates = "users",
        cascade="all, delete-orphan")
    
    macrocycles = db.relationship(
        "User_Macrocycles",
        back_populates = "users",
        passive_deletes=True)

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