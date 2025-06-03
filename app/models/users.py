from app import db, login_manager
from flask_login import UserMixin
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, EmailMixin, PasswordMixin

from sqlalchemy.dialects.postgresql import TEXT

class Users(BaseModel, TableNameMixin, EmailMixin, PasswordMixin, UserMixin):
    # Fields 
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

    # Relationships
    equipment = db.relationship(
        "User_Equipment", 
        back_populates="users", 
        cascade="all, delete")

    exercises = db.relationship(
        "User_Exercises", 
        back_populates="users", 
        cascade="all, delete")

    availability = db.relationship(
        "User_Weekday_Availability", 
        back_populates="users", 
        cascade="all, delete")

    macrocycles = db.relationship(
        "User_Macrocycles", 
        back_populates="users", 
        cascade="all, delete")

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