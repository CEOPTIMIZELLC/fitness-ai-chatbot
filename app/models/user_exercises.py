from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin

class User_Exercises(db.Model, TableNameMixin):
    """Exercise available to a user during a training period."""
    __table_args__ = {'comment': "The exercises that a user has performed."}

    # Fields
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    one_rep_max = db.Column(db.Numeric(10, 2), nullable=False, default=10, comment='The maximum weight that the user can lift for one repetition of the exercise.')
    one_rep_load = db.Column(db.Numeric(10, 2), nullable=False, default=10, comment='The weight that the user can lift for one repetition of the exercise.')
    volume = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment='sets * reps * load')
    density = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment='working duration / duration')
    intensity = db.Column(db.Integer, nullable=False, default=100, comment='The intensity of the exercise in comparison to the their one rep max.')
    performance = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment='intensity * volume')

    # Relationships
    users = db.relationship("Users", back_populates="exercises")
    exercises = db.relationship("Exercise_Library", back_populates="users")

    def to_dict(self):
        return {
            "user_id": self.user_id, 
            "exercise_id": self.exercise_id, 
            "exercise_name": self.exercises.name,
            "one_rep_max": self.one_rep_max,
            "one_rep_load": self.one_rep_load,
            "volume": self.volume,
            "density": self.density,
            "intensity": self.intensity,
            "performance": self.performance,
        }
