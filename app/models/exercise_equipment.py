from app import db
from app.models.mixins import TableNameMixin

class Exercise_Equipment_Base(db.Model):
    __abstract__ = True
    
    """The base class for exercise equipment."""
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment_library.id", ondelete='CASCADE'), primary_key=True)

    quantity = db.Column(db.Integer, nullable=False, comment='The number of the equipment required for the exercise.')
    equipment_relationship = db.Column(db.String(50), comment='E.g., And, Or')

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id, 
            "exercise_name": self.exercises.name, 
            "equipment_id": self.equipment_id, 
            "equipment_name": self.equipment.name, 
            "quantity": self.quantity, 
            "equipment_relationship": self.equipment_relationship
        }


# The table of supportive equipment that is required to perform an exercise.
class Exercise_Supportive_Equipment(Exercise_Equipment_Base, TableNameMixin):
    """The supportive equipment that is required to perform an exercise."""
    __table_args__ = {'comment': "The supportive equipment that is required to perform an exercise."}
    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="supportive_equipment")
    equipment = db.relationship("Equipment_Library", back_populates="supportive_for_exercises")


# The table of assistive equipment that is required to perform an exercise.
class Exercise_Assistive_Equipment(Exercise_Equipment_Base, TableNameMixin):
    """The assistive equipment that is required to perform an exercise."""
    __table_args__ = {'comment': "The assistive equipment that is required to perform an exercise."}
    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="assistive_equipment")
    equipment = db.relationship("Equipment_Library", back_populates="assistive_for_exercises")


# The table of weighted equipment that is required to perform an exercise.
class Exercise_Weighted_Equipment(Exercise_Equipment_Base, TableNameMixin):
    """The weighted equipment that is required to perform an exercise."""
    __table_args__ = {'comment': "The weighted equipment that is required to perform an exercise."}
    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="weighted_equipment")
    equipment = db.relationship("Equipment_Library", back_populates="weighted_for_exercises")


# The table of marking equipment that is required to perform an exercise.
class Exercise_Marking_Equipment(Exercise_Equipment_Base, TableNameMixin):
    """The marking equipment that is required to perform an exercise."""
    __table_args__ = {'comment': "The marking equipment that is required to perform an exercise."}
    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="marking_equipment")
    equipment = db.relationship("Equipment_Library", back_populates="marking_for_exercises")


# The table of other equipment that is required to perform an exercise.
class Exercise_Other_Equipment(Exercise_Equipment_Base, TableNameMixin):
    """The other equipment that is required to perform an exercise."""
    __table_args__ = {'comment': "The other equipment that is required to perform an exercise."}
    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="other_equipment")
    equipment = db.relationship("Equipment_Library", back_populates="other_for_exercises")
