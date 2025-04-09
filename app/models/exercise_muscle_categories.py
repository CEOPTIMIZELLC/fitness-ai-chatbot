from app import db
from app.models.mixins import TableNameMixin

class ExerciseJoinBase(db.Model):
    __abstract__ = True

    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            f"{self._target_name}_id": getattr(self, f"{self._target_name}_id"),
            f"{self._target_name}_name": getattr(getattr(self, f"{self._target_plural}"), "name")
        }

class Exercise_Bodyparts(ExerciseJoinBase, TableNameMixin):
    __table_args__ = {'comment': "The join table for exercises and bodyparts."}
    
    _target_name = "bodypart"
    _target_plural = "bodyparts"

    # Fields
    bodypart_id = db.Column(db.Integer, db.ForeignKey("bodypart_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="bodyparts")
    bodyparts = db.relationship("Bodypart_Library", back_populates="exercises")

class Exercise_Body_Regions(ExerciseJoinBase, TableNameMixin):
    __table_args__ = {'comment': "The join table for exercises and body regions."}

    _target_name = "body_region"
    _target_plural = "body_regions"

    # Fields
    body_region_id = db.Column(db.Integer, db.ForeignKey("body_region_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="body_regions")
    body_regions = db.relationship("Body_Region_Library", back_populates="exercises")

class Exercise_Muscle_Groups(ExerciseJoinBase, TableNameMixin):
    __table_args__ = {'comment': "The join table for exercises and muscle groups."}

    _target_name = "muscle_group"
    _target_plural = "muscle_groups"

    # Fields
    muscle_group_id = db.Column(db.Integer, db.ForeignKey("muscle_group_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="muscle_groups")
    muscle_groups = db.relationship("Muscle_Group_Library", back_populates="exercises")

class Exercise_Muscles(ExerciseJoinBase, TableNameMixin):
    __table_args__ = {'comment': "The join table for exercises and muscles."}

    _target_name = "muscle"
    _target_plural = "muscles"

    # Fields
    muscle_id = db.Column(db.Integer, db.ForeignKey("muscle_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="muscles")
    muscles = db.relationship("Muscle_Library", back_populates="exercises")



