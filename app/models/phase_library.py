from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

# The phases that exist.
class Phase_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The phases that a mesocycle may be tagged with."}
    # Fields
    phase_duration_minimum_in_weeks = db.Column(
        db.Interval, 
        nullable=False, 
        comment='The minimum number of weeks that the phase can last. E.g., {"2 weeks", "4 weeks", "8 weeks"}')

    phase_duration_maximum_in_weeks = db.Column(
        db.Interval, 
        nullable=False, 
        comment='The maximum number of weeks that the phase can last. E.g., {"2 weeks", "4 weeks", "8 weeks"}')

    # Relationships
    phase_components = db.relationship(
        "Phase_Component_Library", 
        back_populates="phases", 
        cascade="all, delete-orphan")

    phase_component_bodyparts = db.relationship(
        "Phase_Component_Bodyparts", 
        back_populates="phases", 
        cascade="all, delete-orphan")

    goals = db.relationship(
        "Goal_Phase_Requirements", 
        back_populates="phases", 
        cascade="all, delete-orphan")

    mesocycles = db.relationship(
        "User_Mesocycles", 
        back_populates="phases", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "phase_duration_minimum_in_weeks": self.phase_duration_minimum_in_weeks.days//7, 
            "phase_duration_maximum_in_weeks": self.phase_duration_maximum_in_weeks.days//7
        }
    