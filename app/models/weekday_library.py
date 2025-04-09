from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

# The days of the week.
class Weekday_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of week days that exist."}
    # Relationships
    availability = db.relationship(
        "User_Weekday_Availability", 
        back_populates="weekdays", 
        cascade="all, delete-orphan")

    workout_days = db.relationship(
        "User_Workout_Days", 
        back_populates="weekdays", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }