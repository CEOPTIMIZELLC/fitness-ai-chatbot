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

    def _log_schedule(self, headers, header_line, schedule):
        schedule_string = ""
        schedule_string += header_line
        for weekday in schedule:
            _line_fields = self._line_fields(weekday)
            schedule_string += self._formatted_entry_line(headers, _line_fields)
        return schedule_string

    def run_printer(self, schedule):
        formatted = ""

        # Calculate longest string sizes
        longest_sizes = {"weekday_name": longest_string_size_for_key(schedule, "weekday_name")}

        # Create headers
        formatted += self.schedule_header
        headers = self._create_header_fields(longest_sizes)
        header_line = self._formatted_header_line(headers)

        formatted += self._log_schedule(headers, header_line, schedule)

        return formatted

def Main(schedule):
    availability_schedule_printer = AvailabilitySchedulePrinter()
    return availability_schedule_printer.run_printer(schedule)