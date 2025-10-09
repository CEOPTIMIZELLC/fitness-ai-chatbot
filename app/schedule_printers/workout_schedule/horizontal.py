class HorizontalSchedulePrinter:
    def _log_horizontal_sub_schedule(self, sub_schedule_name, headers, header_line, schedule, warmup=False):
        sub_schedule_list = []
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

                set_var = exercise["sets"]
                for set in range(1, set_var+1):
                    _line_fields = self._line_fields(component_count, exercise, set, superset_var)
                    sub_schedule_list.append(_line_fields)
                    sub_schedule_string += self._formatted_entry_line(headers, _line_fields)
        return sub_schedule_list, sub_schedule_string

    def _log_horizontal_main_schedule(self, headers, header_line, schedule):
        return self._log_horizontal_sub_schedule(
            sub_schedule_name="Workout", 
            headers=headers, 
            header_line=header_line, 
            schedule=schedule, 
            warmup=False
        )