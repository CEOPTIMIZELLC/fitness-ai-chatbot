from app import db
from datetime import timedelta

from sqlalchemy.ext.hybrid import hybrid_property

# The phases that exist.
class User_Exercises(db.Model):
    """The workout components belonging to a user's workout day. This also acts as a join table between a workout day and the phase components types."""
    # Fields
    __table_args__ = {
        'comment': "Workout components for a workout day."
    }
    __tablename__ = "user_exercises"
    id = db.Column(db.Integer, primary_key=True)
    workout_day_id = db.Column(db.Integer, db.ForeignKey("user_workout_days.id", ondelete='CASCADE'), nullable=False)
    phase_component_id = db.Column(db.Integer, db.ForeignKey("phase_component_library.id"), nullable=False)
    #exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id"), nullable=False)

    order = db.Column(
        db.Integer,
        comment='The order of the workout_component for the current workout_day.')

    reps = db.Column(
        db.Integer, 
        nullable=False,
        comment='The number of repetitions for a single exercise for the phase subcomponent.')

    sets = db.Column(
        db.Integer, 
        nullable=False,
        comment='The number of sets of repetitions for a single exercise for the phase subcomponent.')

    intensity = db.Column(
        db.Integer, 
        comment='The amount of intensity for a single exercise for the phase subcomponent.')

    rest = db.Column(
        db.Integer, 
        nullable=False,
        comment='The amount of time to rest for a single exercise for the phase subcomponent.')

    exercises_per_bodypart = db.Column(
        db.Integer, 
        comment='The number of exercises per bodypart included for the phase component.')


    # Relationships
    workout_days = db.relationship(
        "User_Workout_Days",
        back_populates = "exercises")

    '''exercises = db.relationship(
        "Exercise_Library",
        back_populates = "workout_days")'''

    phase_components = db.relationship(
        "Phase_Component_Library",
        back_populates = "user_exercises")

    def to_dict(self):
        return {
            "id": self.id,
            "workout_day_id": self.workout_day_id,
            "phase_component_id": self.phase_component_id,
            "phase_component_subcomponent": self.phase_components.sub_component,
            #"exercise_id": self.exercise_id,
            #"exercise_name": self.exercises.name,
            "order": self.order,
            "reps": self.reps,
            "sets": self.sets,
            "intensity": self.intensity,
            "rest": self.rest,
            "exercises_per_bodypart": self.exercises_per_bodypart
        }