from app import db
from app.models.mixins import LibraryMixin

# The components that exist for phase components.
class Bodypart_Library(db.Model, LibraryMixin):
    __table_args__ = {
        'comment': "The library of components that exist for phase components."
    }
    # Fields
    __tablename__ = "bodypart_library"

    # Relationships
    categories = db.relationship(
        "Muscle_Categories", 
        back_populates="bodyparts", 
        cascade="all, delete-orphan")

    exercises = db.relationship(
        "Exercise_Bodyparts", 
        back_populates="bodyparts", 
        cascade="all, delete-orphan")

    phase_component_bodyparts = db.relationship(
        "Phase_Component_Bodyparts", 
        back_populates="bodyparts", 
        cascade="all, delete-orphan")

    workout_components = db.relationship(
        "User_Workout_Components", 
        back_populates="bodyparts", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }