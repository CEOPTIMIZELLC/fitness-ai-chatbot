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
    
    severity = db.Column(
        JSONB,
        nullable=False,
        comment='E.g., {"mild": "2 weeks", "moderate": "4 weeks", "severe": "8 weeks"}')
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity
        }
