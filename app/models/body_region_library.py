from app import db
from app.models.mixins import LibraryMixin

class Body_Region_Library(db.Model, LibraryMixin):
    __table_args__ = {
        'comment': "The library of body regions."
    }
    # Fields
    __tablename__ = "body_region_library"

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