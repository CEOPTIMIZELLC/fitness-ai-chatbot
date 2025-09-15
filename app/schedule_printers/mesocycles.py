from app.utils.longest_string import longest_string_size_for_key
from .base import BaseSchedulePrinter

class MesocycleSchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("Mesocycle", 12),
            "phase": ("Phase", longest_sizes["phase"] + 4),
            "start_date": ("Start Date", 17),
            "end_date": ("End Date", 17),
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

    def _retrieve_longest_schedule_elements(self, schedule):
        return {
            "phase": longest_string_size_for_key(schedule, "phase_name")
        }

def Main(schedule):
    mesocycle_schedule_printer = MesocycleSchedulePrinter()
    return mesocycle_schedule_printer.run_printer(schedule)