from app.utils.longest_string import longest_string_size_for_key
from .base import BaseSchedulePrinter

class MicrocycleSchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self) -> dict:
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

    def _log_schedule(self, headers, header_line, schedule):
        schedule_string = ""
        schedule_string += header_line
        for user_microcycle in schedule:
            _line_fields = self._line_fields(user_microcycle)
            schedule_string += self._formatted_entry_line(headers, _line_fields)
        return schedule_string

    def run_printer(self, schedule):
        formatted = ""

        # Create headers
        formatted += self.schedule_header
        headers = self._create_header_fields()
        header_line = self._formatted_header_line(headers)

        formatted += self._log_schedule(headers, header_line, schedule)

        return formatted

def Main(schedule):
    mesocycle_schedule_printer = MicrocycleSchedulePrinter()
    return mesocycle_schedule_printer.run_printer(schedule)