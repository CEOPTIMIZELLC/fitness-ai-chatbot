from app import db
from .mixins import OrderedMixin

# The phases that exist.
class User_Workout_Days(db.Model, OrderedMixin):
    """The workout days belonging to a user's microcycle. This also acts as a join table between a microcycle and the phase components types."""
    # Fields
    __table_args__ = {
        'comment': "Workout days for a microcycle."
    }
    __tablename__ = "user_workout_days"
    id = db.Column(db.Integer, primary_key=True)
    microcycle_id = db.Column(db.Integer, db.ForeignKey("user_microcycles.id", ondelete='CASCADE'), nullable=False)
    weekday_id = db.Column(db.Integer, db.ForeignKey("weekday_library.id", ondelete='CASCADE'), nullable=False)

    date = db.Column(
        db.Date, 
        default=db.func.current_timestamp(), 
        nullable=False, 
        comment='Date that the workout_day should start.')

    # Relationships
    weekdays = db.relationship("Weekday_Library", back_populates="workout_days")
    microcycles = db.relationship("User_Microcycles", back_populates="workout_days")
    workout_components = db.relationship(
        "User_Workout_Components", 
        back_populates="workout_days", 
        cascade="all, delete-orphan")

    exercises = db.relationship(
        "User_Exercises", 
        back_populates="workout_days", 
        cascade="all, delete-orphan")

    def to_dict(self):
        components = []
        for workout_component in self.workout_components:
            components.append(workout_component.to_dict())
        exercises = []
        for exercise in self.exercises:
            exercises.append(exercise.to_dict())
        return {
            "id": self.id, 
            "microcycle_id": self.microcycle_id, 
            "weekday_id": self.weekday_id, 
            "weekday_name": self.weekdays.name, 
            "order": self.order, 
            "date": self.date, 
            "components": components, 
            "exercises": exercises
        }