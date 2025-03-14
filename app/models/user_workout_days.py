from app import db
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import TEXT
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
    microcycle_id = db.Column(db.Integer, db.ForeignKey("user_microcycles.id"), nullable=False)
    phase_component_id = db.Column(db.Integer, db.ForeignKey("phase_components.id"), nullable=False)

    order = db.Column(
        db.Integer, 
        nullable=False,
        comment='The order of the workout_day for the current microcycle.')

    start_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp(), 
        nullable=False,
        comment='Date that the workout_day should start.')

    end_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp() + timedelta(weeks=26), 
        nullable=False,
        comment='Date that the workout_day should end.')

    # Duration of the workday based on the current start and end date.
    @hybrid_property
    def duration(self):
        return self.end_date - self.start_date

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
            "order": self.order,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "duration": str(self.duration)
        }