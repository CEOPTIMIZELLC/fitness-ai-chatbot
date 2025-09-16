from app.utils.longest_string import longest_string_size_for_key
from .base import BaseSchedulePrinter

class MacrocycleSchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("Macrocycle", 13),
            "goal_name": ("Goal", longest_sizes["goal_name"] + 4),
            "start_date": ("Start", 17),
            "end_date": ("End", 17),
            "duration": ("Duration", 20)
        }

    def _line_fields(self, goal):
        return {
            "number": str(str(goal["id"])),
            "goal_name": f"{goal['goal_name']}",
            "start_date": str(goal["start_date"]),
            "end_date": str(goal["end_date"]),
            "duration": f"{str(goal["duration"])}"
        }

    def _retrieve_longest_schedule_elements(self, schedule):
        return {
            "goal_name": longest_string_size_for_key(schedule, "goal_name")
        }

def Main(schedule):
    macrocycle_schedule_printer = MacrocycleSchedulePrinter()
    return macrocycle_schedule_printer.run_printer(schedule)