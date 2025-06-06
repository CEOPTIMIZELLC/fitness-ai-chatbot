from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin
from sqlalchemy.dialects.postgresql import TEXT

# The loading systems that exist.
class Loading_System_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of loading systems that exists."}
    # Fields
    description = db.Column(
        TEXT, 
        nullable=False, 
        comment='Description for the loading system.')
    
    # Relationships
    workout_days = db.relationship(
        "User_Workout_Days", 
        back_populates="loading_systems", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "description": self.description
        }