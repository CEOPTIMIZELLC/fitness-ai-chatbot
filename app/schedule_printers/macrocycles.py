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

    def _log_schedule(self, headers, header_line, schedule):
        schedule_string = ""
        schedule_string += header_line
        for goal in schedule:
            _line_fields = self._line_fields(goal)
            schedule_string += self._formatted_entry_line(headers, _line_fields)
        return schedule_string

    def run_printer(self, schedule):
        formatted = ""

        # Calculate longest string sizes
        longest_sizes = {"goal_name": longest_string_size_for_key(schedule, "goal_name")}

        # Create headers
        formatted += self.schedule_header
        headers = self._create_header_fields(longest_sizes)
        header_line = self._formatted_header_line(headers)

        formatted += self._log_schedule(headers, header_line, schedule)

        return formatted

def Main(schedule):
    macrocycle_schedule_printer = MacrocycleSchedulePrinter()
    return macrocycle_schedule_printer.run_printer(schedule)