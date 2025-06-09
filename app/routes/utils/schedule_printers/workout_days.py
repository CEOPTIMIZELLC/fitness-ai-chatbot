from app.utils.longest_string import longest_string_size_for_key

def _create_formatted_field(label: str, value: str, header_length: int) -> str:
    """Helper method to create consistently formatted fields"""
    prefix = "| " if label != "#" else ""
    formatted = f"{prefix}{value}"
    return f"{formatted:<{header_length}}"

def _create_header_fields(longest_sizes: dict) -> dict:
    """Create all header fields with consistent formatting"""
    return {
        "number": ("Component", 12),
        "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
        "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
        "duration": ("Duration", 35)
    }

def formatted_header_line(headers):
    header_line = ""
    for label, (text, length) in headers.items():
        header_line += _create_formatted_field(text, text, length)
    return header_line

def log_day(current_day, header_line):
    line = ""
    current_order = str(current_day["order"])
    current_date = str(current_day["date"])
    current_name = f"{current_day["weekday_name"]:<{10}}"
    line += f"\n| Day {current_order} | {current_name} | {current_date} | \n"
    line += header_line + "\n"
    return line

def formatted_schedule(headers, component_count, pc):
    line = ""

    # Format line
    line_fields = {
        "number": str(component_count + 1),
        "phase_component": f"{pc['phase_component_subcomponent']}",
        "bodypart": pc["bodypart_name"],
        "duration": f"{pc["duration"]} sec"
    }

    for field, (_, length) in headers.items():
        line += _create_formatted_field(field, line_fields[field], length)
    return line + "\n"

def Main(phase_components, bodyparts, schedule):
    formatted = ""

    # Calculate longest string sizes
    longest_sizes = {
        "phase_component": longest_string_size_for_key(phase_components, "name"),
        "bodypart": longest_string_size_for_key(bodyparts, "name")
    }

    # Create headers
    headers = _create_header_fields(longest_sizes)

    # Create header line
    formatted += "\nFinal Training Schedule:\n" + "-" * 40 + "\n"
    header_line = formatted_header_line(headers)

    for current_day in schedule:
        current_components = current_day["components"]
        if current_components:
            formatted += log_day(current_day, header_line)
            for i, component in enumerate(current_components):
                formatted += formatted_schedule(headers, i, component)

    return formatted