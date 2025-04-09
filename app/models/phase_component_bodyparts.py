from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin

# The components that exist and their bodyparts..
class Phase_Component_Bodyparts(BaseModel, TableNameMixin):
    __table_args__ = {'comment': "The library of phase components that exists."}
    # Fields
    phase_id = db.Column(db.Integer, db.ForeignKey("phase_library.id"), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey("component_library.id"), nullable=False)
    bodypart_id = db.Column(db.Integer, db.ForeignKey("bodypart_library.id"), nullable=False)

    required_within_microcycle = db.Column(
        db.String(50), 
        nullable=False, 
        comment='Whether or not the phase component is required for every microcycle.')

    # Relationships
    phases = db.relationship("Phase_Library", back_populates="phase_component_bodyparts")
    components = db.relationship("Component_Library", back_populates="phase_component_bodyparts")
    bodyparts = db.relationship("Bodypart_Library", back_populates="phase_component_bodyparts")

    def to_dict(self):
        return {
            "id": self.id, 
            "phase_id": self.phase_id, 
            "phase_name": self.phases.name, 
            "component_id": self.component_id, 
            "component_name": self.components.name, 
            "bodypart_id": self.bodypart_id, 
            "bodypart_name": self.bodyparts.name, 
            "required_within_microcycle": self.required_within_microcycle, 
        }