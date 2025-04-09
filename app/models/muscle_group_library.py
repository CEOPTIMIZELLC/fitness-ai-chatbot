from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

class Muscle_Group_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of muscle groups."}
    # Relationships
    categories = db.relationship(
        "Muscle_Categories", 
        back_populates="muscle_groups", 
        cascade="all, delete-orphan")

    exercises = db.relationship(
        "Exercise_Muscle_Groups", 
        back_populates="muscle_groups", 
        cascade="all, delete-orphan")


    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }