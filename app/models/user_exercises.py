from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin

class User_Exercises(BaseModel, TableNameMixin):
    """Exercise available to a user during a training period."""
    __table_args__ = {'comment': "The exercises that a user has performed."}

    # Fields
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), nullable=False)
    one_rep_max = db.Column(db.Integer, nullable=False, default=5, comment='The maximum weight that the user can lift for one repetition of the exercise.')

    # Relationships
    users = db.relationship("Users", back_populates="exercises")
    exercises = db.relationship("Exercise_Library", back_populates="users")

    def to_dict(self):
        return {
            "id": self.id, 
            "user_id": self.user_id, 
            "exercise_id": self.exercise_id, 
            "exercise_name": self.exercises.name,
            "one_rep_max": self.one_rep_max
        }