from app.utils.common_table_queries import user_possible_exercises_with_user_exercise_info

dummy_exercise = {
    "id": 0,
    "name": "Inactive",
    "base_strain": 0,
    "technical_difficulty": 0,
    "component_ids": 0,
    "subcomponent_ids": 0,
    "pc_ids": 0,
    "body_region_ids": None,
    "bodypart_ids": None,
    "muscle_group_ids": None,
    "muscle_ids": None,
    "supportive_equipment_ids": None,
    "supportive_equipment_measurements": None,
    "assistive_equipment_ids": None,
    "assistive_equipment_measurements": None,
    "weighted_equipment_ids": None,
    "weighted_equipment_measurements": [0],
    "is_weighted": False,
    "marking_equipment_ids": None,
    "marking_equipment_measurements": None,
    "other_equipment_ids": None,
    "other_equipment_measurements": None,
    "one_rep_max": 0,
    "one_rep_load": 0,
    "volume": 0,
    "density": 0,                               # Scaled up to avoid floating point errors from model.
    "intensity": 0,
    "performance": 0,                           # Scaled up to avoid floating point errors from model.
    "duration": 0,
    "working_duration": 0,
}

def exercise_dict(exercise, user_exercise):
    # Construct list of allowed weighted measurements.
    weighted_equipment_measurements = [0]
    for key in user_exercise.has_weighted_equipment[1]:
        weighted_equipment_measurements.extend(user_exercise.has_weighted_equipment[1][key])

    """Format the exercise data."""
    return {
        "id": exercise.id,
        "name": exercise.name.lower(),
        "base_strain": exercise.base_strain,
        "technical_difficulty": exercise.technical_difficulty,
        "component_ids": [component_phase.component_id for component_phase in exercise.component_phases],
        "subcomponent_ids": [component_phase.subcomponent_id for component_phase in exercise.component_phases],
        "pc_ids": [[component_phase.component_id, component_phase.subcomponent_id] for component_phase in exercise.component_phases],
        "body_region_ids": exercise.all_body_region_ids,
        "bodypart_ids": exercise.all_bodypart_ids,
        "muscle_group_ids": exercise.all_muscle_group_ids,
        "muscle_ids": exercise.all_muscle_ids,
        "supportive_equipment_ids": exercise.all_supportive_equipment,
        "supportive_equipment_measurements": user_exercise.has_supportive_equipment[1],
        "assistive_equipment_ids": exercise.all_assistive_equipment,
        "assistive_equipment_measurements": user_exercise.has_assistive_equipment[1],
        "weighted_equipment_ids": exercise.all_weighted_equipment,
        "weighted_equipment_measurements": weighted_equipment_measurements,
        "is_weighted": exercise.is_weighted,
        "marking_equipment_ids": exercise.all_marking_equipment,
        "marking_equipment_measurements": user_exercise.has_marking_equipment[1],
        "other_equipment_ids": exercise.all_other_equipment,
        "other_equipment_measurements": user_exercise.has_other_equipment[1],
        "one_rep_max": user_exercise.decayed_one_rep_max,
        "one_rep_load": user_exercise.one_rep_load,
        "volume": user_exercise.volume,
        "density": int(user_exercise.density * 100),                                    # Scaled up to avoid floating point errors from model.
        "intensity": user_exercise.intensity,
        "performance": int(user_exercise.decayed_performance * 100),                    # Scaled up to avoid floating point errors from model.
        "duration": user_exercise.duration,
        "working_duration": user_exercise.working_duration,
    }

# Retrieve the phase types and their corresponding constraints for a goal.
def construct_available_exercises_list(exercises_with_component_phases):
    possible_exercises_list = [dummy_exercise]
    for exercise, user_exercise in exercises_with_component_phases:
        possible_exercises_list.append(exercise_dict(exercise, user_exercise))
    return possible_exercises_list

def Main(user_id):
    exercises_with_component_phases = user_possible_exercises_with_user_exercise_info(user_id)
    return construct_available_exercises_list(exercises_with_component_phases)
