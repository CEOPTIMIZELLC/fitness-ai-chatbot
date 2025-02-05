from app import db

# The table of measurements that apply to a piece of equipment.
class Equipment_Measurements(db.Model):
    # Fields
    __tablename__ = "equipment_measurements"

    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment_library.id"), primary_key=True)
    measurement_id = db.Column(db.Integer, db.ForeignKey("measurement_types.id"), primary_key=True)
    
    # Relationships
    measurements = db.relationship(
        "Measurement_Types",
        back_populates = "equipment")
    
    equipment = db.relationship(
        "Equipment_Library",
        back_populates = "measurements")
    
    def to_dict(self):
        return {
            "measurement_name": self.measurements.name,
            "measurement_unit": self.measurements.unit,
            "equipment_name": self.equipment.name
        }