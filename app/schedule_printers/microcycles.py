from app.utils.longest_string import longest_string_size_for_key
from .base import BaseSchedulePrinter

class MicrocycleSchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("Microcycle", 13),
            "start_date": ("Start", 17),
            "end_date": ("End", 17),
            "duration": ("Duration", 20)
        }

    def _line_fields(self, microcycle):
        return {
            "number": str(str(microcycle["order"])),
            "start_date": str(microcycle["start_date"]),
            "end_date": str(microcycle["end_date"]),
            "duration": f"{str(microcycle["duration"])}"
        }

    def _retrieve_longest_schedule_elements(self, schedule):
        return {}

def Main(schedule):
    mesocycle_schedule_printer = MicrocycleSchedulePrinter()
    return mesocycle_schedule_printer.run_printer(schedule)