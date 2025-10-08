def parse_seconds_to_hr_min_sec(duration):
    duration_seconds = duration % 60
    duration = duration // 60
    duration_minutes = duration % 60
    duration_hours = duration // 60

    return {
        "hours": duration_hours,
        "minutes": duration_minutes,
        "seconds": duration_seconds,
    }

def parse_time_dict(time_dict=0):
    return ", ".join(
        "{:02}".format(value) + f" {key}"
        for key, value in time_dict.items()
        if value
    )