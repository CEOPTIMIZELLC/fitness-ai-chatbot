from app import db
from datetime import timedelta

from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, DateRangeMixin, OrderedMixin

# The phases that exist.
class User_Microcycles(BaseModel, TableNameMixin, DateRangeMixin, OrderedMixin):
    """The microcycles belonging to a user's mesocycle."""
    __table_args__ = {'comment': "Microcycles for a mesocycle."}
    # Fields
    mesocycle_id = db.Column(db.Integer, db.ForeignKey("user_mesocycles.id", ondelete='CASCADE'), nullable=False)

    end_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp() + timedelta(weeks=1), 
        nullable=False, 
        comment='Date that the microcyc should end.')

    # Relationships
    mesocycles = db.relationship("User_Mesocycles", back_populates="microcycles")
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