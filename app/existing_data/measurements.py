from app.models import Measurement_Types, Equipment_Measurements

measurements = [
    Measurement_Types(name="weight", unit="kilograms"),
    Measurement_Types(name="length", unit="centimeters"),
    Measurement_Types(name="height", unit="centimeters")
]

equipment_measurements = [
    Equipment_Measurements(equipment_id=1, measurement_id=1),
    Equipment_Measurements(equipment_id=1, measurement_id=2),
    Equipment_Measurements(equipment_id=2, measurement_id=2)
]
