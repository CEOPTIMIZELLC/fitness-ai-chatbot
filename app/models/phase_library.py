from app import db

# The phases that exist.
class Phase_Library(db.Model):
    # Fields
    __table_args__ = {
        'comment': "The phases that a mesocycle may be tagged with."
    }
    __tablename__ = "phase_library"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False, 
        comment='E.g., Stabilization Endurance, Strength Endurance, Hypertrophy, Maximal Strength, Power')
    
    phase_duration_minimum_in_weeks = db.Column(
        db.Integer, 
        nullable=False, 
        comment='The minimum number of weeks that the phase can last.')
    
    phase_duration_maximum_in_weeks = db.Column(
        db.Integer, 
        nullable=False, 
        comment='The maximum number of weeks that the phase can last.')
    
    # Relationships
    goals = db.relationship(
        "Goal_Phase_Requirements",
        back_populates = "phases",
        cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phase_duration_minimum_in_weeks": self.phase_duration_minimum_in_weeks,
            "phase_duration_maximum_in_weeks": self.phase_duration_maximum_in_weeks
        }
    