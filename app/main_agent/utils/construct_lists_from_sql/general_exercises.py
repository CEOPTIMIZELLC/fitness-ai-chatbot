from tqdm import tqdm
dummy_general_exercise = {
    "id": 0,
    "name": "Inactive",
}

def general_exercise_dict(possible_exercise):
    # Construct list of allowed weighted measurements.

    """Format the exercise data."""
    return {
        "id": possible_exercise["general_id"],
        "name": possible_exercise["general_name"],
    }

def Main(possible_exercises):
    unique_general_exercises = {}
    for possible_exercise in tqdm(possible_exercises, total=len(possible_exercises), desc="Creating general exercise list from entries"):
        general_id = possible_exercise.get("general_id")
        general_name = possible_exercise.get("general_name")
        if general_id not in unique_general_exercises:
            unique_general_exercises[general_id] = general_name
    return unique_general_exercises