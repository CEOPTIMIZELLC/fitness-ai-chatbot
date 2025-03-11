from app import db
from sqlalchemy.dialects.postgresql import JSONB

# The subcomponents that exist for phase components.
class Phase_Subcomponents_Library(db.Model):
    __table_args__ = {
        'comment': "The library of subcomponents that exist for phase components."
    }
    # Fields
    __tablename__ = "phase_subcomponents_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False)

    # Relationships
    phase_components = db.relationship(
        "Phase_Components",
        back_populates = "subcomponents",
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }