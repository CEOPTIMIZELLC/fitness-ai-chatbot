from app import db

# The table of assistive equipment that is required to perform an exercise.
class Exercise_Assistive_Equipment(db.Model):
    """The assistive equipment that is required to perform an exercise."""
    __table_args__ = {
        'comment': "The assistive equipment that is required to perform an exercise."
    }
    # Fields
    __tablename__ = "exercise_assistive_equipment"

    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment_library.id", ondelete='CASCADE'), primary_key=True)

    quantity = db.Column(
        db.Integer, 
        nullable=False,
        comment='The number of the equipment required for the exercise.')

    equipment_relationship = db.Column(
        db.String(50), 
        comment='E.g., And, Or')

    # Relationships
    exercises = db.relationship(
        "Exercise_Library",
        back_populates = "assistive_equipment")
    
    equipment = db.relationship(
        "Equipment_Library",
        back_populates = "assistive_for_exercises")
    
    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "equipment_id": self.equipment_id,
            "equipment_name": self.equipment.name,
            "quantity": self.quantity,
            "equipment_relationship": self.equipment_relationship
        }