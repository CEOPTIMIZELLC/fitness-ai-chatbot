from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

class Muscle_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of muscles."}
    # Relationships
    categories = db.relationship(
        "Muscle_Categories", 
        back_populates="muscles", 
        cascade="all, delete-orphan")

    exercises = db.relationship(
        "Exercise_Muscles", 
        back_populates="muscles", 
        cascade="all, delete-orphan")


    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }