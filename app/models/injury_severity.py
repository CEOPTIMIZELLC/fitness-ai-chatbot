from app import db

# The timescale of injuries.
class Injury_Severity(db.Model):
    """How much time an injury will take to recover from based on severity."""
    # Fields
    __tablename__ = "injury_severity"
    injury_id = db.Column(db.Integer, db.ForeignKey("injury_library.id"), primary_key=True)
    severity_id = db.Column(db.Integer, db.ForeignKey("severity_library.id"), primary_key=True)
    
    estimated_time_to_recovery = db.Column(
        db.String(50),
        nullable=False,
        comment='E.g., {"2 weeks", "4 weeks", "8 weeks"}')
    
    injuries = db.relationship(
        "Injury_Library",
        back_populates = "severity")
    
    severity = db.relationship(
        "Severity_Library",
        back_populates = "injuries")
    
    def to_dict(self):
        return {
            "injury_name": self.injuries.name,
            "severity_name": self.severity.name,
            "estimated_time_to_recovery": self.estimated_time_to_recovery
        }