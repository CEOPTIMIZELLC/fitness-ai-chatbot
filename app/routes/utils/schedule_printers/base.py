class BaseSchedulePrinter:
    schedule_header = "\nFORMATTED SCHEDULE:\n" + "-" * 40 + "\n"

    def _create_formatted_field(self, label: str, value: str, header_length: int) -> str:
        """Helper method to create consistently formatted fields"""
        prefix = "| " if label != "#" else ""
        formatted = f"{prefix}{value}"
        return f"{formatted:<{header_length}}"

    def formatted_header_line(self, headers):
        header_line = ""
        for label, (text, length) in headers.items():
            header_line += self._create_formatted_field(text, text, length)
        return header_line + "\n"
    
    def formatted_entry_line(self, headers, line_fields):
        line = ""
        for field, (_, length) in headers.items():
            line += self._create_formatted_field(field, line_fields[field], length)
        return line + "\n"
