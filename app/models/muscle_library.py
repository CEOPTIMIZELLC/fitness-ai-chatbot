from app import db
from app.models.mixins import LibraryMixin

class Muscle_Library(db.Model, LibraryMixin):
    __table_args__ = {
        'comment': "The library of muscles."
    }
    # Fields
    __tablename__ = "muscle_library"

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