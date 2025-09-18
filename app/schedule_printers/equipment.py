from app.utils.longest_string import longest_string_size_for_key
from .base import BaseSchedulePrinter

class EquipmentSchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "id": ("Unique ID", 14),
            "equipment": ("Equipment", longest_sizes["equipment"] + 4),
            "measurement": ("Measurement", 15),
            "unit_of_measurement": ("Unit of Measurement", 23),
        }

    def _line_fields(self, equipment):
        item_measurement = equipment.get("measurement", "-")
        item_unit_of_measurement = equipment.get("unit_of_measurement", "-")

        return {
            "id": str(equipment["id"]),
            "equipment": f"{equipment['equipment_name']}",
            "measurement": str(item_measurement),
            "unit_of_measurement": item_unit_of_measurement,
        }

    def _retrieve_longest_schedule_elements(self, schedule):
        return {
            "equipment": longest_string_size_for_key(schedule, "equipment_name")
        }

def Main(schedule):
    equipment_schedule_printer = EquipmentSchedulePrinter()
    return equipment_schedule_printer.run_printer(schedule)