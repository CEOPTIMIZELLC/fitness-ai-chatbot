from config import ScheduleDisplayConfig
from app.utils.longest_string import longest_string_size_for_key
from app.utils.time_parser import parse_seconds_to_hr_min_sec, parse_time_dict
from app.schedule_printers.base import BaseSchedulePrinter

non_specific_true_flags = {
    True: "True Exercise", 
    False: "False Exercise"
}

class WorkoutScheduleListPrinter(BaseSchedulePrinter):
    def _create_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "number": ("No", 5),
            "true_exercise_flag": ("True Flag", longest_sizes["true_exercise_flag"] + 4),
            "exercise": ("Exercise", longest_sizes["exercise"] + 4),
            "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
            "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
            "warmup": ("Warmup", 9),
            "duration": ("Duration", len("xx hours, xx minutes, xx.xx seconds") + 4),
            "working_duration": ("WDuration", len("xx hours, xx minutes, xx.xx seconds") + 4),
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

        # Whether or not a specific indication should be given for if the exercise belongs to the phase component/bodypart combination.
        if ScheduleDisplayConfig.specific_true_exercise_flag:
            # Display a specific indication.
            true_exercise_flag = exercise["true_exercise_flag"]
        else:
            # Display a non specific indication.
            true_exercise_flag = non_specific_true_flags[exercise["true_exercise_flag"] == "True Exercise"]

        duration_dict = parse_seconds_to_hr_min_sec(exercise["duration"])
        working_duration_duration_dict = parse_seconds_to_hr_min_sec(exercise["working_duration"])

        # Format line
        return {
            "number": str(i + 1),
            "exercise": exercise["exercise_name"],
            "true_exercise_flag": true_exercise_flag,
            "phase_component": f"{exercise['phase_component_subcomponent']}",
            "bodypart": exercise["bodypart_name"],
            "warmup": f"{exercise["is_warmup"]}",
            "duration": parse_time_dict(duration_dict),
            "working_duration": parse_time_dict(working_duration_duration_dict),
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

    def _retrieve_longest_schedule_elements(self, schedule):
        # Calculate longest string sizes
        longest_sizes = {
            "phase_component": longest_string_size_for_key(schedule, "phase_component_subcomponent"),
            "bodypart": longest_string_size_for_key(schedule, "bodypart_name"),
            "exercise": longest_string_size_for_key(schedule, "exercise_name"),
        }

        # The size of the column depends on if the specific flags are allowed.
        if ScheduleDisplayConfig.specific_true_exercise_flag:
            # The column should be the size of the longest flag in the schedule.
            longest_sizes["true_exercise_flag"] = longest_string_size_for_key(schedule, "true_exercise_flag")
        else:
            # The column should be the size of the longest non-specific flag allowed.
            longest_sizes["true_exercise_flag"] = len("False Exercise")

        return longest_sizes

def Main(schedule):
    exercise_schedule_printer = WorkoutScheduleListPrinter()
    return exercise_schedule_printer.run_printer(schedule)