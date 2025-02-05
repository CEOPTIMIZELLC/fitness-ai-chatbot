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
    
    # Relationships
    exercises = db.relationship(
        "Exercise_Equipment",
        back_populates = "equipment",
        cascade="all, delete-orphan")

    measurements = db.relationship(
        "Equipment_Measurements",
        back_populates = "equipment",
        cascade="all, delete-orphan")
        

    training_available_equipment = db.relationship(
        "User_Training_Available_Equipment",
        back_populates = "equipment",
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "equipment_measure": self.equipment_measure
        }