from app.utils.longest_string import longest_string_size_for_key
from app.utils.time_parser import parse_seconds_to_hr_min_sec, parse_time_dict
from .base import BaseSchedulePrinter

from app.models import Bodypart_Library, Phase_Component_Library
from app.utils.db_helpers import get_all_items

class PhaseComponentSchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("Component", 12),
            "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
            "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
            "duration": ("Duration", 35)
        }

    def _line_fields(self, component_count, pc):
        duration_dict = parse_seconds_to_hr_min_sec(pc["duration"])
        return {
            "number": str(component_count + 1),
            "phase_component": f"{pc['phase_component_subcomponent']}",
            "bodypart": pc["bodypart_name"],
            "duration": parse_time_dict(duration_dict)
        }

    def _log_day(self, current_day, duration):
        current_order = str(current_day["order"])
        current_date = f"{str(current_day["date"]):<{14}}"
        current_name = f"{current_day["weekday_name"]:<{10}}"
        duration_dict = parse_seconds_to_hr_min_sec(duration)
        parsed_duration = parse_time_dict(duration_dict)
        current_duration = f"{parsed_duration:<{len("xx hours, xx minutes, xx.xx seconds") + 4}}"
        return f"\n| Day {current_order} | {current_name} | {current_date} | {current_duration} | \n"

    def _log_schedule(self, headers, header_line, schedule):
        schedule_list = []
        schedule_string = ""
        for current_day in schedule:
            current_components = current_day["components"]
            if current_components:
                day_duration = 0
                pc_list = []
                pc_string = ""
                for i, component in enumerate(current_components):
                    day_duration += component["duration"]
                    _line_fields = self._line_fields(i, component)
                    pc_list.append(_line_fields)
                    pc_string += self._formatted_entry_line(headers, _line_fields)
                day_string = self._log_day(current_day, day_duration)
                schedule_list.append(day_string)
                schedule_list.append(pc_list)
                schedule_string += f"{day_string}{header_line}\n{pc_string}"
        return schedule_list, schedule_string

    def _retrieve_longest_schedule_elements(self, schedule):
        phase_components = get_all_items(Phase_Component_Library)
        bodyparts = get_all_items(Bodypart_Library)

        return {
            "phase_component": longest_string_size_for_key(phase_components, "name"),
            "bodypart": longest_string_size_for_key(bodyparts, "name")
        }

def Main(phase_components):
    workout_day_schedule_printer = PhaseComponentSchedulePrinter()
    return workout_day_schedule_printer.run_printer(phase_components)