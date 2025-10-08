from app.utils.longest_string import longest_string_size_for_key
from app.utils.time_parser import parse_seconds_to_hr_min_sec, parse_time_dict
from .base import BaseSchedulePrinter

class AvailabilitySchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("No", 7),
            "weekday_name": ("Weekday", longest_sizes["weekday_name"] + 4),
            "availability": ("Availability", len("xx hours, xx minutes, xx.xx seconds") + 4),
        }

    def _line_fields(self, weekday):
        availability_dict = parse_seconds_to_hr_min_sec(weekday["availability"])
        return {
            "number": str(str(weekday["weekday_id"])),
            "weekday_name": f"{weekday['weekday_name']}",
            "availability": parse_time_dict(availability_dict)
        }

    def _retrieve_longest_schedule_elements(self, schedule):
        return {
            "weekday_name": longest_string_size_for_key(schedule, "weekday_name")
        }

def Main(schedule):
    availability_schedule_printer = AvailabilitySchedulePrinter()
    return availability_schedule_printer.run_printer(schedule)