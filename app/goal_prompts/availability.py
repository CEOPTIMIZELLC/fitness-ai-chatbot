from .utils import retrieve_system_prompt

availability_request = {
    "description": """**Availability** - Changes to their weekly or daily availability (e.g., new days or times they can train).""", 
    "ex_output": """- `availability`: is_requested = true, detail = "User is no longer available on Wednesdays." """}

availability_system_prompt = retrieve_system_prompt(availability_request)