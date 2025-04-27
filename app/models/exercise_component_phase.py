from app import db
from app.models.mixins import TableNameMixin

# The join table for exercises and its .
class Exercise_Component_Phases(db.Model, TableNameMixin):
    """The component and subcomponent combination that are attached to an exercise. that is required to perform an exercise."""
    __table_args__ = {'comment': "The phase component-subcomponent combination that applies to an exercise."}

    # Fields
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component_library.id", ondelete='CASCADE'), primary_key=True)
    subcomponent_id = db.Column(db.Integer, db.ForeignKey("subcomponent_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates="component_phases")
    components = db.relationship("Component_Library", back_populates="exercises")
    subcomponents = db.relationship("Subcomponent_Library", back_populates="exercises")

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id, 
            "exercise_name": self.exercises.name, 
            "component_id": self.component_id, 
            "component_name": self.components.name, 
            "subcomponent_id": self.subcomponent_id, 
            "subcomponent_name": self.subcomponents.name
        }
