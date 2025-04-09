from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

class Body_Region_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of body regions."}
    # Relationships
    categories = db.relationship(
        "Muscle_Categories", 
        back_populates="body_regions", 
        cascade="all, delete-orphan")

    exercises = db.relationship(
        "Exercise_Body_Regions", 
        back_populates="body_regions", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }