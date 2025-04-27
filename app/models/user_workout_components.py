from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin

# The phases that exist.
class User_Workout_Components(BaseModel, TableNameMixin):
    """The workout components belonging to a user's workout day. This also acts as a join table between a workout day and the phase components types."""
    __table_args__ = {'comment': "Workout components for a workout day."}
    # Fields
    workout_day_id = db.Column(db.Integer, db.ForeignKey("user_workout_days.id", ondelete='CASCADE'), nullable=False)
    phase_component_id = db.Column(db.Integer, db.ForeignKey("phase_component_library.id"), nullable=False)
    bodypart_id = db.Column(db.Integer, db.ForeignKey("bodypart_library.id"), nullable=False)

    duration = db.Column(
        db.Integer, 
        nullable=False, 
        comment='The duration that the phase component is projected to last.')


    # Relationships
    workout_days = db.relationship("User_Workout_Days", back_populates="workout_components")
    phase_components = db.relationship("Phase_Component_Library", back_populates="workout_components")
    bodyparts = db.relationship("Bodypart_Library", back_populates="workout_components")

    def to_dict(self):
        return {
            "id": self.id, 
            "workout_day_id": self.workout_day_id, 
            "phase_component_id": self.phase_component_id, 
            "phase_component_subcomponent": self.phase_components.name, 
            "bodypart_id": self.bodypart_id, 
            "bodypart_name": self.bodyparts.name, 
            "duration": self.duration
        }