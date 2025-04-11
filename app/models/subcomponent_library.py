from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

# The subcomponents that exist for phase components.
class Subcomponent_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of subcomponents that exist for phase components."}
    # Fields
    density = db.Column(db.Integer, nullable=False, comment='')
    volume = db.Column(db.Integer, nullable=False, comment='')
    load = db.Column(db.Integer, nullable=False, comment='')
    explanation = db.Column(db.String(255), comment='')

    # Relationships
    phase_components = db.relationship(
        "Phase_Component_Library", 
        back_populates="subcomponents", 
        cascade="all, delete-orphan")

    exercises = db.relationship(
        "Exercise_Component_Phases", 
        back_populates="subcomponents", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "density": self.density, 
            "volume": self.volume, 
            "load": self.load, 
            "explanation": self.explanation
        }