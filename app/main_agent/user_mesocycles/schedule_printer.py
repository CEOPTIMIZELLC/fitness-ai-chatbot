from app.utils.longest_string import longest_string_size_for_key
from app.main_agent.schedule_printer import BaseSchedulePrinter

class SchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("Mesocycle", 12),
            "phase": ("Phase", longest_sizes["phase"] + 4),
            "start_date": ("Start", 17),
            "end_date": ("End", 17),
            "duration": ("Duration", 20),
            "goal_duration": ("Goal Duration", 20),
        }

    def _line_fields(self, phase):
        return {
            "number": str(str(phase["order"])),
            "phase": f"{phase['phase_name']}",
            "start_date": str(phase["start_date"]),
            "end_date": str(phase["end_date"]),
            "duration": f"{str(phase["duration"])}",
            "goal_duration": f"+{str(phase["duration"]) if phase['is_goal_phase'] else 0}"
        }

    def _log_schedule(self, headers, header_line, schedule):
        schedule_string = ""
        schedule_string += header_line
        for phase in schedule:
            _line_fields = self._line_fields(phase)
            schedule_string += self._formatted_entry_line(headers, _line_fields)
        return schedule_string

    def run_schedule_printer(self, schedule):
        formatted = ""

        # Calculate longest string sizes
        longest_sizes = {"phase": longest_string_size_for_key(schedule, "phase_name")}

        # Create headers
        formatted += self.schedule_header
        headers = self._create_header_fields(longest_sizes)
        header_line = self._formatted_header_line(headers)

        formatted += self._log_schedule(headers, header_line, schedule)

        return formatted

def Main(schedule):
    mesocycle_schedule_printer = SchedulePrinter()
    return mesocycle_schedule_printer.run_schedule_printer(schedule)