from app import db

# The equipment that exist.
class Measurement_Types(db.Model):
    # Fields
    __tablename__ = "measurement_types"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        comment='E.g., weight, height')
    
    unit = db.Column(
        db.String(50),
        nullable=False,
        comment='E.g., kilograms, centimeters')
    
    # Relationships
    equipment = db.relationship(
        "Equipment_Measurements",
        back_populates = "measurements",
        cascade="all, delete-orphan")
    
    training_equipment = db.relationship(
        "User_Training_Equipment_Measurements",
        back_populates = "measurements",
        cascade="all, delete-orphan")
    
    
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "unit": self.unit
        }