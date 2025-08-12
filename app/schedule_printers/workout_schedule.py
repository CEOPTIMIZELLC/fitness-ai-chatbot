from app.utils.longest_string import longest_string_size_for_key
from .base import BaseSchedulePrinter

class WorkoutScheduleSchedulePrinter(BaseSchedulePrinter):
    def _create_final_header_fields(self, longest_sizes: dict) -> dict:
        """Create all header fields with consistent formatting"""
        return {
            "superset": ("Sub", 6),
            "set": ("Set", 6),
            "number": ("No", 5),
            "true_exercise_flag": ("True Flag", longest_sizes["true_exercise_flag"] + 4),
            "exercise": ("Exercise", longest_sizes["exercise"] + 4),
            "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
            "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
            "warmup": ("Warmup", 9),
            "duration": ("Duration", 12),
            "working_duration": ("WDuration", 12),
            "base_strain": ("BStrain", 10),
            "seconds_per_exercise": ("Sec/Exer", 11),
            "reps": ("Reps", 7),
            "rest": ("Rest", 7),
            "one_rep_max": ("1RM", 6),
            "training_weight": ("Weight", 9),
            "intensity": ("Intensity", 12),
            "volume": ("Volume", 9),
            "density": ("Density", 10),
            "performance": ("Performance", 14),
            "end": ("", 2),
        }


    def _line_fields(self, i, exercise, set_count, superset_var):
        new_weight = exercise["weight"] or 0

        one_rep_max = int(round((new_weight * (30 + exercise["reps"])) / 30, 2))

        # Format line
        return {
            "set": str(set_count),
            "superset": str(superset_var["superset_current"]) if superset_var["is_resistance"] else str(superset_var["not_a_superset"]),
            "number": str(i + 1),
            "exercise": exercise["exercise_name"],
            "true_exercise_flag": exercise["true_exercise_flag"],
            "phase_component": f"{exercise['phase_component_subcomponent']}",
            "bodypart": exercise["bodypart_name"],
            "warmup": f"{exercise["is_warmup"]}",
            "duration": f"{exercise["duration"] // exercise["sets"]} sec",
            "working_duration": f"{exercise["working_duration"] // exercise["sets"]} sec",
            "base_strain": str(exercise["base_strain"]),
            "seconds_per_exercise": f"{exercise["seconds_per_exercise"]} sec",
            "reps": str(exercise["reps"]),
            "rest": str(exercise["rest"]),
            "one_rep_max": str(one_rep_max) if one_rep_max else "",
            "training_weight": str(exercise["weight"]) if exercise["weight"] else "",
            "intensity": str(exercise["intensity"]) if exercise["intensity"] else "",
            "volume": str(exercise["volume"]),
            "density": str(exercise["density"]),
            "performance": str(exercise["performance"]),
            "end": "",
        }

    def _check_if_component_is_resistance(self, component_id, bodypart_id, superset_var):
        # Check if the current component is resistance.
        if component_id == 6:
            superset_var["is_resistance"] = True

            # Count up the superset count if a new superset is encountered.
            if superset_var["bodypart_id"] != bodypart_id:
                superset_var["superset_current"] += 1
            
            superset_var["bodypart_id"] = bodypart_id
        else:
            superset_var["is_resistance"] = False
        return superset_var

    def _log_sub_schedule(self, sub_schedule_name, headers, header_line, schedule, warmup=False, set_count=None):
        sub_schedule_string = ""
        # Create header line
        sub_schedule_string += f"\n| {sub_schedule_name} |\n"
        sub_schedule_string += header_line

        superset_var = {
            "not_a_superset": "-", 
            "superset_current": 0, 
            "superset_previous": 0, 
            "bodypart_id": 0,
            "is_resistance": False}

        for component_count, exercise in enumerate(schedule):
            sub_schedule_part = exercise["is_warmup"] if warmup else not exercise["is_warmup"]
            if sub_schedule_part:
                # Count the number of occurrences of each phase component
                superset_var["superset_previous"] = superset_var["superset_current"]

                # Check if the current component is resistance.
                superset_var = self._check_if_component_is_resistance(exercise["component_id"], exercise["bodypart_id"], superset_var)

                if set_count:
                    _line_fields = self._line_fields(component_count, exercise, set_count, superset_var)
                    sub_schedule_string += self._formatted_entry_line(headers, _line_fields)
                else:
                    set_var = exercise["sets"]
                    for set in range(1, set_var+1):
                        _line_fields = self._line_fields(component_count, exercise, set, superset_var)
                        sub_schedule_string += self._formatted_entry_line(headers, _line_fields)
        return sub_schedule_string

    def _log_schedule(self, headers, header_line, loading_system_id, schedule):
        schedule_string = ""
        max_sets = max(exercise["sets"] if not exercise["is_warmup"] else 1 for exercise in schedule)

        # Create header line
        sub_schedule_name = "Warm-Up"

        schedule_string += self._log_sub_schedule(sub_schedule_name, headers, header_line, schedule, True)

        # Different logging method depending on if the schedule is vertical.
        if loading_system_id == 1:
            for set_count in range(1, max_sets+1):
                sub_schedule_name = f"Vertical Set {set_count}"
                schedule_string += self._log_sub_schedule(sub_schedule_name, headers, header_line, schedule, False, set_count)
        else:
            sub_schedule_name = f"Workout"
            schedule_string += self._log_sub_schedule(sub_schedule_name, headers, header_line, schedule, False)
        return schedule_string

    def run_schedule_printer(self, workout_date, loading_system_id, schedule):
        formatted = f"Workout for {str(workout_date)}"

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

        formatted += self._log_schedule(headers, header_line, loading_system_id, schedule)

        return formatted

def Main(workout_date, loading_system_id, schedule):
    exercise_schedule_printer = WorkoutScheduleSchedulePrinter()
    return exercise_schedule_printer.run_schedule_printer(workout_date, loading_system_id, schedule)