from app import db

# The levels of severity an injury can have.
class Severity_Library(db.Model):
    """Library of levels of severity that exist."""
    # Fields
    __tablename__ = "severity_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        comment='E.g., Mild, Moderate, Severe')

    # Relationships
    injuries = db.relationship(
        "Injury_Severity",
        back_populates = "severity",
        cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }