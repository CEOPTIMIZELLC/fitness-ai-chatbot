from app import db
from sqlalchemy.dialects.postgresql import JSONB

# The equipment that exist.
class Equipment_Library(db.Model):
    # Fields
    __tablename__ = "equipment_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        comment='E.g., Barbell, Dumbbell, Resistance Band')
    
    equipment_measure = db.Column(
        JSONB,
        nullable=False,
        comment='E.g., {"weight": "kg", "height": "cm"}')
    
    # Relationships
    exercises = db.relationship(
        "Exercise_Equipment",
        back_populates = "equipment",
        cascade="all, delete-orphan")
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "equipment_measure": self.equipment_measure
        }

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