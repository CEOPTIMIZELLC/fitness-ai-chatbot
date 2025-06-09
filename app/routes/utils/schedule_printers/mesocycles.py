from app.utils.longest_string import longest_string_size_for_key


def _create_formatted_field(label: str, value: str, header_length: int) -> str:
    """Helper method to create consistently formatted fields"""
    prefix = "| " if label != "#" else ""
    formatted = f"{prefix}{value}"
    return f"{formatted:<{header_length}}"

def _create_header_fields(longest_sizes: dict) -> dict:
    """Create all header fields with consistent formatting"""
    return {
        "number": ("Mesocycle", 12),
        "phase": ("Phase", longest_sizes["phase"] + 4),
        "start_date": ("Start", 17),
        "end_date": ("End", 17),
        "duration": ("Duration", 20),
        "goal_duration": ("Goal Duration", 20),
    }

def log_entry(headers, phase):
    # Format line
    line_fields = {
        "number": str(str(phase["order"])),
        "phase": f"{phase['phase_name']}",
        "start_date": str(phase["start_date"]),
        "end_date": str(phase["end_date"]),
        "duration": f"{str(phase["duration"])}",
        "goal_duration": f"+{str(phase["duration"]) if phase['is_goal_phase'] else 0}"
    }

    line = ""
    for field, (_, length) in headers.items():
        line += _create_formatted_field(field, line_fields[field], length)
    return line + "\n"

def formatted_header_line(headers):
    # Create header line
    schedule_header = "\nFinal Training Schedule:\n" + "-" * 40 + "\n"
    header_line = ""
    for label, (text, length) in headers.items():
        header_line += _create_formatted_field(text, text, length)
    schedule_header += header_line + "\n"
    return schedule_header

def Main(schedule):
    formatted = ""

    # Calculate longest string sizes
    longest_sizes = {"phase": longest_string_size_for_key(schedule, "phase_name")}

    # Create headers
    headers = _create_header_fields(longest_sizes)
    formatted += formatted_header_line(headers)

    for i, phase in enumerate(schedule):
        formatted += log_entry(headers, phase)

    return formatted