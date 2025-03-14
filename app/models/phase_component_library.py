from app import db
from sqlalchemy.dialects.postgresql import JSONB

# The components that exist for phase components.
class Phase_Component_Library(db.Model):
    __table_args__ = {
        'comment': "The library of components that exist for phase components."
    }
    # Fields
    __tablename__ = "phase_component_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False)

    # Relationships
    phase_components = db.relationship(
        "Phase_Components",
        back_populates = "components",
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }