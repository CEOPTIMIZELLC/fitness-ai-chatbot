from app import db
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import TEXT

# The phases that exist.
class User_Mesocycles(db.Model):
    """The mesocycles belonging to a user's macrocycle. This also acts as a join table between a macrocycle and the phase types."""
    # Fields
    __table_args__ = {
        'comment': "Mesocycles for a macrocycle."
    }
    __tablename__ = "user_mesocycles"
    id = db.Column(db.Integer, primary_key=True)
    macrocycle_id = db.Column(db.Integer, db.ForeignKey("user_macrocycles.id"), nullable=False)
    phase_id = db.Column(db.Integer, db.ForeignKey("phase_library.id"), nullable=False)

    start_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp(), 
        nullable=False,
        comment='Date that the mesocycle should start.')
    
    end_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp() + timedelta(weeks=26), 
        nullable=False,
        comment='Date that the mesocycle should end.')

    # Relationships
    macrocycles = db.relationship(
        "User_Macrocycles",
        back_populates = "mesocycles")
    
    phases = db.relationship(
        "Phase_Library",
        back_populates = "mesocycles")
    
    def to_dict(self):
        return {
            "macrocycle_id": self.macrocycle_id,
            "phase_name": self.phases.name,
            "start_date": self.start_date,
            "end_date": self.end_date
        }