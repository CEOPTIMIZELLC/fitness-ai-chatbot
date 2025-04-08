from app import db
from sqlalchemy.ext.hybrid import hybrid_property

from .mixins import OrderedMixin

# The phases that exist.
class User_Exercises(db.Model, OrderedMixin):
    """The workout components belonging to a user's workout day. This also acts as a join table between a workout day and the phase components types."""
    # Fields
    __table_args__ = {
        'comment': "Workout components for a workout day."
    }
    __tablename__ = "user_exercises"
    id = db.Column(db.Integer, primary_key=True)
    workout_day_id = db.Column(db.Integer, db.ForeignKey("user_workout_days.id", ondelete='CASCADE'), nullable=False)
    phase_component_id = db.Column(db.Integer, db.ForeignKey("phase_component_library.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id"), nullable=False)

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


    # Seconds per exercise of the exercise.
    @hybrid_property
    def seconds_per_exercise(self):
        return self.phase_components.seconds_per_exercise

    # Base strain of the exercise.
    @hybrid_property
    def base_strain(self):
        return self.exercises.base_strain

    # Duration of the exercise.
    @hybrid_property
    def duration(self):
        return (self.seconds_per_exercise * self.reps + self.rest) * self.sets

    # Working duration of the exercise.
    @hybrid_property
    def working_duration(self):
        return self.seconds_per_exercise * self.reps * self.sets

    # Duration of the exercise based on the formula adjusted with strain.
    @hybrid_property
    def strained_duration(self):
        return (self.seconds_per_exercise * (1 + self.base_strain / 10) * self.reps + self.rest) * self.sets

    # Working duration of the exercise based on the formula adjusted with strain.
    @hybrid_property
    def strained_working_duration(self):
        return self.seconds_per_exercise * (1 + self.base_strain / 10) * self.reps * self.sets
    
    # Strain of the exercise overall.
    @hybrid_property
    def strain(self):
        return self.strained_duration / self.strained_working_duration

    # Relationships
    workout_days = db.relationship("User_Workout_Days", back_populates="exercises")
    exercises = db.relationship("Exercise_Library", back_populates="user_exercises")
    phase_components = db.relationship("Phase_Component_Library", back_populates="user_exercises")

    def to_dict(self):
        return {
            "id": self.id, 
            "workout_day_id": self.workout_day_id, 
            "phase_component_id": self.phase_component_id, 
            "phase_component_subcomponent": self.phase_components.name, 
            "exercise_id": self.exercise_id, 
            "exercise_name": self.exercises.name, 
            "order": self.order, 
            "seconds_per_exercise": self.seconds_per_exercise, 
            "base_strain": self.base_strain, 
            "reps": self.reps, 
            "sets": self.sets, 
            "intensity": self.intensity, 
            "rest": self.rest, 
            "duration": self.duration, 
            "working_duration": self.working_duration, 
            "strained_duration": self.strained_duration, 
            "strained_working_duration": self.strained_working_duration, 
            "strain": self.strain
        }