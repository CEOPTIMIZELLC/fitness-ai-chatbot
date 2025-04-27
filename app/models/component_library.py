from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

# The components that exist for phase components.
class Component_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of components that exist for phase components."}
    # Relationships
    phase_components = db.relationship(
        "Phase_Component_Library", 
        back_populates="components", 
        cascade="all, delete-orphan")

    phase_component_bodyparts = db.relationship(
        "Phase_Component_Bodyparts", 
        back_populates="components", 
        cascade="all, delete-orphan")

    exercises = db.relationship(
        "Exercise_Component_Phases", 
        back_populates="components", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }