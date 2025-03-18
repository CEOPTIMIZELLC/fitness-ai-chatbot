from app import db
from datetime import timedelta

from sqlalchemy.ext.hybrid import hybrid_property

# The phases that exist.
class User_Workout_Days(db.Model):
    """The workout days belonging to a user's microcycle. This also acts as a join table between a microcycle and the phase components types."""
    # Fields
    __table_args__ = {
        'comment': "Workout days for a microcycle."
    }
    __tablename__ = "user_workout_days"
    id = db.Column(db.Integer, primary_key=True)
    microcycle_id = db.Column(db.Integer, db.ForeignKey("user_microcycles.id", ondelete='CASCADE'), nullable=False)
    phase_component_id = db.Column(db.Integer, db.ForeignKey("phase_components.id"), nullable=False)

    order = db.Column(
        db.Integer, 
        nullable=False,
        comment='The order of the workout_day for the current microcycle.')

    date = db.Column(
        db.Date, 
        default=db.func.current_timestamp(), 
        nullable=False,
        comment='Date that the workout_day should start.')

    exercise_count = db.Column(
        db.Integer, 
        nullable=False,
        comment='The number of different exercises for the phase subcomponent.')

    rep = db.Column(
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

    exercises_per_bodypart_workout = db.Column(
        db.Integer, 
        comment='The number of exercises per bodypart included for the phase component.')


    # Relationships
    microcycles = db.relationship(
        "User_Microcycles",
        back_populates = "workout_days")

    phase_components = db.relationship(
        "Phase_Component_Library",
        back_populates = "workout_days")

    def to_dict(self):
        return {
            "id": self.id,
            "microcycle_id": self.microcycle_id,
            "phase_component_id": self.phase_component_id,
            "phase_component_subcomponent": self.phase_components.sub_component,
            "date": self.date,
            "order": self.order,
            "exercise_count": self.exercise_count,
            "rep": self.rep,
            "sets": self.sets,
            "intensity": self.intensity,
            "rest": self.rest,
            "exercises_per_bodypart_workout": self.exercises_per_bodypart_workout
        }