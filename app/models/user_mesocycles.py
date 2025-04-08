from app import db
from datetime import timedelta

from sqlalchemy.ext.hybrid import hybrid_property

# The phases that exist.
class User_Mesocycles(db.Model):
    """The mesocycles belonging to a user's macrocycle. This also acts as a join table between a macrocycle and the phase types."""
    # Fields
    __table_args__ = {
        'comment': "Mesocycles for a macrocycle."
    }
    __tablename__ = "user_mesocycles"
    id = db.Column(db.Integer, primary_key=True)
    macrocycle_id = db.Column(db.Integer, db.ForeignKey("user_macrocycles.id", ondelete='CASCADE'), nullable=False)
    phase_id = db.Column(db.Integer, db.ForeignKey("phase_library.id"), nullable=False)

    order = db.Column(
        db.Integer, 
        nullable=False, 
        comment='The order of the mesocycle for the current macrocycle.')

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

    # Duration of the mesocycle based on the current start and end date.
    @hybrid_property
    def duration(self):
        return self.end_date - self.start_date

    # Relationships
    phases = db.relationship(
        "Phase_Library", 
        back_populates="mesocycles")

    macrocycles = db.relationship(
        "User_Macrocycles", 
        back_populates="mesocycles")

    microcycles = db.relationship(
        "User_Microcycles", 
        back_populates="mesocycles", 
        cascade="all, delete-orphan")

    def to_dict(self):
        total_duration = self.duration
        return {
            "id": self.id, 
            "macrocycle_id": self.macrocycle_id, 
            "order": self.order, 
            "phase_id": self.phase_id, 
            "phase_name": self.phases.name, 
            "start_date": self.start_date, 
            "end_date": self.end_date, 
            "duration": f"{total_duration.days // 7} weeks {total_duration.days % 7} days"
        }