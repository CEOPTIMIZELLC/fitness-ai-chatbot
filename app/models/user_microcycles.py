from app import db
from datetime import timedelta
from sqlalchemy.ext.hybrid import hybrid_property

# The phases that exist.
class User_Microcycles(db.Model):
    """The microcycles belonging to a user's mesocycle."""
    # Fields
    __table_args__ = {
        'comment': "Microcycles for a mesocycle."
    }
    __tablename__ = "user_microcycles"
    id = db.Column(db.Integer, primary_key=True)
    mesocycle_id = db.Column(db.Integer, db.ForeignKey("user_mesocycles.id", ondelete='CASCADE'), nullable=False)

    order = db.Column(
        db.Integer, 
        nullable=False, 
        comment='The order of the microcycle for the current mesocycle.')

    start_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp(), 
        nullable=False, 
        comment='Date that the microcycle should start.')

    end_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp() + timedelta(weeks=7), 
        nullable=False, 
        comment='Date that the microcycle should end.')

    # Duration of the microcycle based on the current start and end date.
    @hybrid_property
    def duration(self):
        return self.end_date - self.start_date
    
    # Relationships
    mesocycles = db.relationship(
        "User_Mesocycles", 
        back_populates="microcycles")

    workout_days = db.relationship(
        "User_Workout_Days", 
        back_populates="microcycles", 
        cascade="all, delete-orphan")

    def to_dict(self):
        total_duration = self.duration
        return {
            "id": self.id, 
            "mesocycle_id": self.mesocycle_id, 
            "order": self.order, 
            "start_date": self.start_date, 
            "end_date": self.end_date, 
            "duration": f"{total_duration.days // 7} weeks {total_duration.days % 7} days"
        }