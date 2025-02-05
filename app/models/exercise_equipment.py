from app import db

# The table of equipment that a exercise currently or previously has.
class Exercise_Equipment(db.Model):
    # Fields
    __tablename__ = "exercise_equipment"

    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id"), primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment_library.id"), primary_key=True)
    
    # Relationships
    exercises = db.relationship(
        "Exercise_Library",
        back_populates = "equipment")
    
    equipment = db.relationship(
        "Equipment_Library",
        back_populates = "exercises")
    
    def to_dict(self):
        return {
            "exercise_name": self.exercises.name,
            "equipment_name": self.equipment.name
        }