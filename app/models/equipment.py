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
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "equipment_measure": self.equipment_measure
        }
