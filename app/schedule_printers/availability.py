from app.utils.longest_string import longest_string_size_for_key
from .base import BaseSchedulePrinter

class AvailabilitySchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("No", 7),
            "weekday_name": ("Weekday", longest_sizes["weekday_name"] + 4),
            "availability": ("Availability", 20),
        }

    def _line_fields(self, weekday):
        return {
            "number": str(str(weekday["weekday_id"])),
            "weekday_name": f"{weekday['weekday_name']}",
            "availability": str(weekday["availability"])
        }

    def _retrieve_longest_schedule_elements(self, schedule):
        return {
            "weekday_name": longest_string_size_for_key(schedule, "weekday_name")
        }

def Main(schedule):
    availability_schedule_printer = AvailabilitySchedulePrinter()
    return availability_schedule_printer.run_printer(schedule)