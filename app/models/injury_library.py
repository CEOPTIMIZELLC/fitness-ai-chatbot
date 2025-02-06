from app import db
from sqlalchemy.dialects.postgresql import JSONB

# The injuries that exist.
class Injury_Library(db.Model):
    """Library of physical injuries that exist."""
    # Fields
    __tablename__ = "injury_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        comment='E.g., Sprained Ankle, Shoulder Strain')
    
    # Relationships
    severity = db.relationship(
        "Injury_Severity",
        back_populates = "injuries",
        cascade="all, delete-orphan")
    
    users = db.relationship(
        "User_Injuries",
        back_populates = "injuries",
        cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity
        }