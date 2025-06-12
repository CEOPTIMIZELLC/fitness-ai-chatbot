from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

# The components that exist for phase components.
class Muscle_Categories(BaseModel, TableNameMixin):
    __table_args__ = {'comment': "The join table for the different muscle groups that exist."}
    # Fields
    muscle_id = db.Column(db.Integer, db.ForeignKey("muscle_library.id", ondelete='CASCADE'), nullable=False)
    muscle_group_id = db.Column(db.Integer, db.ForeignKey("muscle_group_library.id", ondelete='CASCADE'), nullable=False)
    bodypart_id = db.Column(db.Integer, db.ForeignKey("bodypart_library.id", ondelete='CASCADE'), nullable=False)
    body_region_id = db.Column(db.Integer, db.ForeignKey("body_region_library.id", ondelete='CASCADE'), nullable=False)

    # Relationships
    muscles = db.relationship("Muscle_Library", back_populates="categories")
    muscle_groups = db.relationship("Muscle_Group_Library", back_populates="categories")
    bodyparts = db.relationship("Bodypart_Library", back_populates="categories")
    body_regions = db.relationship("Body_Region_Library", back_populates="categories")

    def to_dict(self):
        return {
            "id": self.id, 
            "muscle_id": self.muscle_id, 
            "muscle_name": self.muscles.name, 
            "muscle_group_id": self.muscle_group_id, 
            "muscle_group_name": self.muscle_groups.name, 
            "bodypart_id": self.bodypart_id, 
            "bodypart_name": self.bodyparts.name,
            "body_region_id": self.body_region_id, 
            "body_region_name": self.body_regions.name, 
        }

class Muscle_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of muscles."}
    # Relationships
    categories = db.relationship("Muscle_Categories", back_populates="muscles", cascade="all, delete-orphan")
    exercises = db.relationship("Exercise_Muscles", back_populates="muscles", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }

class Muscle_Group_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of muscle groups."}
    # Relationships
    categories = db.relationship("Muscle_Categories", back_populates="muscle_groups", cascade="all, delete-orphan")
    exercises = db.relationship("Exercise_Muscle_Groups", back_populates="muscle_groups", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }

# The components that exist for phase components.
class Bodypart_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of components that exist for phase components."}
    # Relationships
    categories = db.relationship("Muscle_Categories", back_populates="bodyparts", cascade="all, delete-orphan")
    exercises = db.relationship("Exercise_Bodyparts", back_populates="bodyparts", cascade="all, delete-orphan")
    phase_component_bodyparts = db.relationship(
        "Phase_Component_Bodyparts", 
        back_populates="bodyparts", 
        cascade="all, delete-orphan")

    workout_components = db.relationship(
        "User_Workout_Components", 
        back_populates="bodyparts", 
        cascade="all, delete-orphan")

    user_workout_exercises = db.relationship(
        "User_Workout_Exercises", 
        back_populates="bodyparts", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }

class Body_Region_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of body regions."}
    # Relationships
    categories = db.relationship("Muscle_Categories", back_populates="body_regions", cascade="all, delete-orphan")
    exercises = db.relationship("Exercise_Body_Regions", back_populates="body_regions", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }