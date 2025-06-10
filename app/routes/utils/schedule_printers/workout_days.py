from app.utils.longest_string import longest_string_size_for_key
from .base import BaseSchedulePrinter

class WorkoutDaySchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("Component", 12),
            "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
            "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
            "duration": ("Duration", 35)
        }

    def line_fields(self, component_count, pc):
        return {
            "number": str(component_count + 1),
            "phase_component": f"{pc['phase_component_subcomponent']}",
            "bodypart": pc["bodypart_name"],
            "duration": f"{pc["duration"]} sec"
        }

    def log_day(self, current_day, header_line):
        line = ""
        current_order = str(current_day["order"])
        current_date = str(current_day["date"])
        current_name = f"{current_day["weekday_name"]:<{10}}"
        line += f"\n| Day {current_order} | {current_name} | {current_date} | \n"
        line += header_line + "\n"
        return line

    def log_schedule(self, headers, header_line, schedule):
        schedule_string = ""
        for current_day in schedule:
            current_components = current_day["components"]
            if current_components:
                schedule_string += self.log_day(current_day, header_line)
                for i, component in enumerate(current_components):
                    line_fields = self.line_fields(i, component)
                    schedule_string += self.formatted_entry_line(headers, line_fields)
        return schedule_string

    def run(self, phase_components, bodyparts, schedule):
        formatted = ""

        # Calculate longest string sizes
        longest_sizes = {
            "phase_component": longest_string_size_for_key(phase_components, "name"),
            "bodypart": longest_string_size_for_key(bodyparts, "name")
        }

        # Create headers
        formatted += self.schedule_header
        headers = self._create_header_fields(longest_sizes)
        header_line = self.formatted_header_line(headers)

        formatted += self.log_schedule(headers, header_line, schedule)

        return formatted

def Main(phase_components, bodyparts, schedule):
    workout_day_schedule_printer = WorkoutDaySchedulePrinter()
    return workout_day_schedule_printer.run(phase_components, bodyparts, schedule)