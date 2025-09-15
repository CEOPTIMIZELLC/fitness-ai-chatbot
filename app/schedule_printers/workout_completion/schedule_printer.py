from app.utils.longest_string import longest_string_size_for_key
from ..base import BaseSchedulePrinter

class WorkoutCompletionSchedulePrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("No", 5),
            "exercise": ("Exercise", longest_sizes["exercise"] + 4),
            "duration": ("Duration", 20),
            "working_duration": ("WDuration", 20),
            "one_rep_max": ("1RM", 17),
            "one_rep_load": ("1R Load", 17),
            "intensity": ("Intensity", 12),
            "volume": ("Volume", 15),
            "density": ("Density", 16),
            "performance": ("Performance", 20),
            "last_performed": ("Last Performed", 30),
            "end": ("", 2),
        }

    def _is_value_present(self, value):
        if value != None:
            return True
        return False

    def _format_transition(self, old_entry, new_entry, key):
        new_value = new_entry[key]
        old_value = old_entry[key]

        new_value_present = self._is_value_present(new_value)
        old_value_present = self._is_value_present(old_value)

        # Return nothing if no value exists for either.
        if (not old_value_present) and (not new_value_present):
            return ""
        
        # Return the transistion value otherwise.
        new_string = str(new_value) if new_value_present else ""
        old_string = str(old_value) if old_value_present else ""
        return f"{old_string} -> {new_string}"

    def _weighted_format_transition(self, old_entry, new_entry, key):
        # Return nothing if no value exists for either.
        if new_entry["is_weighted"]:
            return self._format_transition(old_entry, new_entry, key)

        return ""

    def _line_fields(self, i, old_entry, new_entry):
        # Format line
        return {
            "number": str(i + 1),
            "exercise": new_entry["exercise_name"],
            "duration": f"{self._format_transition(old_entry, new_entry, "duration")} sec",
            "working_duration": f"{self._format_transition(old_entry, new_entry, "working_duration")} sec",
            "one_rep_max": self._weighted_format_transition(old_entry, new_entry, "one_rep_max_decayed"),
            "one_rep_load": self._weighted_format_transition(old_entry, new_entry, "one_rep_load"),
            "intensity": self._weighted_format_transition(old_entry, new_entry, "intensity"),
            "volume": self._format_transition(old_entry, new_entry, "volume"),
            "density": self._format_transition(old_entry, new_entry, "density"),
            "performance": self._format_transition(old_entry, new_entry, "performance_decayed"),
            "last_performed": self._format_transition(old_entry, new_entry, "last_performed"),
            "end": "",
        }

    def _log_schedule(self, headers, header_line, schedule_old, schedule):
        schedule_string = ""
        schedule_string += header_line
        for i, (old_entry, new_entry) in enumerate(zip(schedule_old, schedule)):
            _line_fields = self._line_fields(i, old_entry, new_entry)
            schedule_string += self._formatted_entry_line(headers, _line_fields)
        return schedule_string

    def run_printer(self, schedule_old, schedule):
        formatted = ""

        # Calculate longest string sizes
        longest_sizes = {"exercise": longest_string_size_for_key(schedule, "exercise_name")}

        # Create headers
        formatted += self.schedule_header
        headers = self._create_header_fields(longest_sizes)
        header_line = self._formatted_header_line(headers)

        formatted += self._log_schedule(headers, header_line, schedule_old, schedule)

        return formatted

def Main(schedule_old, schedule):
    completed_exercise_schedule_printer = WorkoutCompletionSchedulePrinter()
    return completed_exercise_schedule_printer.run_printer(schedule_old, schedule)