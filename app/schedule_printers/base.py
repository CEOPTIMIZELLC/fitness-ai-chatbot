class BaseSchedulePrinter:
    schedule_header = "\n" + "-" * 40 + "\n"

    def _create_formatted_field(self, label: str, value: str, header_length: int) -> str:
        """Helper method to create consistently formatted fields"""
        prefix = "| " if label != "#" else ""
        formatted = f"{prefix}{value}"
        return f"{formatted:<{header_length}}"

    def _formatted_header_line(self, headers):
        header_line = ""
        for label, (text, length) in headers.items():
            header_line += self._create_formatted_field(text, text, length)
        return header_line + "\n"
    
    def _formatted_entry_line(self, headers, _line_fields):
        line = ""
        for field, (_, length) in headers.items():
            line += self._create_formatted_field(field, _line_fields[field], length)
        return line + "\n"

    def _retrieve_longest_schedule_elements(self, schedule):
        return {}

    def _create_header_fields(self, longest_sizes: dict) -> dict:
        pass

    def _line_fields(self, item):
        pass

    def _log_schedule(self, headers, header_line, schedule):
        schedule_string = ""
        schedule_string += header_line
        for item in schedule:
            _line_fields = self._line_fields(item)
            schedule_string += self._formatted_entry_line(headers, _line_fields)
        return schedule_string

    def run_printer(self, schedule):
        formatted = ""

        # Calculate longest string sizes
        longest_sizes = self._retrieve_longest_schedule_elements(schedule)

        # Create headers
        formatted += self.schedule_header
        headers = self._create_header_fields(longest_sizes)
        header_line = self._formatted_header_line(headers)

        formatted += self._log_schedule(headers, header_line, schedule)

        return formatted