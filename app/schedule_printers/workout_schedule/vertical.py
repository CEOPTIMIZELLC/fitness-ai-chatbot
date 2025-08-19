class VerticalSchedulePrinter:
    def _log_vertical_sub_schedule(self, sub_schedule_name, headers, header_line, schedule, set_count):
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
            if not exercise["is_warmup"]:
                # Count the number of occurrences of each phase component
                superset_var["superset_previous"] = superset_var["superset_current"]

                # Check if the current component is resistance.
                superset_var = self._check_if_component_is_resistance(exercise["component_id"], exercise["bodypart_id"], superset_var)

                _line_fields = self._line_fields(component_count, exercise, set_count, superset_var)
                sub_schedule_string += self._formatted_entry_line(headers, _line_fields)
        return sub_schedule_string

    def _log_vertical_main_schedule(self, headers, header_line, schedule):
        schedule_string = ""
        max_sets = max(exercise["sets"] if not exercise["is_warmup"] else 1 for exercise in schedule)

        for set_count in range(1, max_sets+1):
            schedule_string += self._log_vertical_sub_schedule(
                sub_schedule_name=f"Vertical Set {set_count}", 
                headers=headers, 
                header_line=header_line, 
                schedule=schedule, 
                set_count=set_count
            )
        return schedule_string