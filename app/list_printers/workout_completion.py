from app.utils.longest_string import longest_string_size_for_key
from app.schedule_printers.base import BaseSchedulePrinter

class WorkoutCompletionListPrinter(BaseSchedulePrinter):
    def _create_final_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("No", 5),
            # "true_exercise_flag": ("True Flag", longest_sizes["true_exercise_flag"] + 4),
            "exercise": ("Exercise", longest_sizes["exercise"] + 4),
            "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
            "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
            "warmup": ("Warmup", 9),
            "duration": ("Duration", 12),
            "working_duration": ("WDuration", 12),
            "base_strain": ("BStrain", 10),
            "seconds_per_exercise": ("Sec/Exer", 11),
            "reps": ("Reps", 7),
            "sets": ("Sets", 10),
            "rest": ("Rest", 7),
            "one_rep_max": ("1RM", 6),
            "training_weight": ("Weight", 9),
            "intensity": ("Intensity", 12),
            "volume": ("Volume", 9),
            "density": ("Density", 10),
            "performance": ("Performance", 14),
            "end": ("", 2),
        }


    def _line_fields(self, i, exercise):
        new_weight = exercise["weight"] or 0

        one_rep_max = int(round((new_weight * (30 + exercise["reps"])) / 30, 2))

        # Format line
        return {
            "number": str(i + 1),
            "exercise": exercise["exercise_name"],
            # "true_exercise_flag": exercise["true_exercise_flag"],
            "phase_component": f"{exercise['phase_component_subcomponent']}",
            "bodypart": exercise["bodypart_name"],
            "warmup": f"{exercise["is_warmup"]}",
            "duration": f"{exercise["duration"]} sec",
            "working_duration": f"{exercise["working_duration"]} sec",
            "base_strain": str(exercise["base_strain"]),
            "seconds_per_exercise": f"{exercise["seconds_per_exercise"]} sec",
            "reps": str(exercise["reps"]),
            "sets": str(exercise["sets"]),
            "rest": str(exercise["rest"]),
            "one_rep_max": str(one_rep_max) if one_rep_max else "",
            "training_weight": str(exercise["weight"]) if exercise["weight"] else "",
            "intensity": str(exercise["intensity"]) if exercise["intensity"] else "",
            "volume": str(exercise["volume"]),
            "density": str(exercise["density"]),
            "performance": str(exercise["performance"]),
            "end": "",
        }

    def _log_schedule(self, headers, header_line, schedule):
        schedule_string = ""
        schedule_string += header_line
        for i, exericse in enumerate(schedule):
            _line_fields = self._line_fields(i, exericse)
            schedule_string += self._formatted_entry_line(headers, _line_fields)
        return schedule_string

    def run_printer(self, schedule):
        formatted = ""

        # Calculate longest string sizes
        longest_sizes = {
            "phase_component": longest_string_size_for_key(schedule, "phase_component_subcomponent"),
            "bodypart": longest_string_size_for_key(schedule, "bodypart_name"),
            "exercise": longest_string_size_for_key(schedule, "exercise_name"),
            "true_exercise_flag": longest_string_size_for_key(schedule, "true_exercise_flag")
        }

        # Create headers
        formatted += self.schedule_header
        headers = self._create_final_header_fields(longest_sizes)
        header_line = self._formatted_header_line(headers)

        formatted += self._log_schedule(headers, header_line, schedule)

        return formatted

def Main(schedule):
    exercise_schedule_printer = WorkoutCompletionListPrinter()
    return exercise_schedule_printer.run_printer(schedule)