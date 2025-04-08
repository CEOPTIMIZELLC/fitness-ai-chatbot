from app import db
from app.models.mixins import LibraryMixin

class Muscle_Group_Library(db.Model, LibraryMixin):
    __table_args__ = {
        'comment': "The library of muscle groups."
    }
    # Fields
    __tablename__ = "muscle_group_library"

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