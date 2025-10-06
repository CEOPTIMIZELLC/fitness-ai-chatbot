from tqdm import tqdm
from app.common_table_queries.exercises import user_possible_exercises_with_user_exercise_info

dummy_exercise = {
    "id": 0,
    "name": "Inactive",
    "general_id": 0,
    "general_name": "Inactive",
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

# Construct all of the component phase combinations for the exercise.
def construct_component_phase_ids(component_phases):
    component_ids = []
    subcomponent_ids = []
    pc_ids = []

    for component_phase in component_phases:
        component_id = component_phase.component_id
        subcomponent_id = component_phase.subcomponent_id

        component_ids.append(component_id)
        subcomponent_ids.append(subcomponent_id)
        pc_ids.append([component_id, subcomponent_id])
    return component_ids, subcomponent_ids, pc_ids

def exercise_dict(exercise, user_exercise):
    # Construct list of allowed weighted measurements.
    weighted_equipment_measurements = [0]
    for key in user_exercise.has_weighted_equipment[1]:
        weighted_equipment_measurements.extend(user_exercise.has_weighted_equipment[1][key])

    # Construct the list of ids.
    component_ids, subcomponent_ids, pc_ids = construct_component_phase_ids(exercise.component_phases)

    """Format the exercise data."""
    return {
        "id": exercise.id,
        "name": exercise.name.lower(),
        "general_id": exercise.general_exercise_id,
        "general_name": exercise.general_exercises.name.lower(),
        "base_strain": exercise.base_strain,
        "technical_difficulty": exercise.technical_difficulty,
        "component_ids": component_ids,
        "subcomponent_ids": subcomponent_ids,
        "pc_ids": pc_ids,
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
        "one_rep_max": user_exercise.one_rep_max_decayed,
        "one_rep_load": user_exercise.one_rep_load,
        "volume": user_exercise.volume,
        "density": int(user_exercise.density * 100),                                    # Scaled up to avoid floating point errors from model.
        "intensity": user_exercise.intensity,
        "performance": int(user_exercise.performance_decayed * 100),                    # Scaled up to avoid floating point errors from model.
        "duration": user_exercise.duration,
        "working_duration": user_exercise.working_duration,
    }

# Retrieve the phase types and their corresponding constraints for a goal.
def construct_available_exercises_list(exercises_with_component_phases):
    possible_exercises_list = [dummy_exercise]
    for exercise, user_exercise in tqdm(exercises_with_component_phases, total=len(exercises_with_component_phases), desc="Creating exercise list from entries"):
        possible_exercises_list.append(exercise_dict(exercise, user_exercise))
    return possible_exercises_list

def Main(user_id):
    # Query List Retrieval
    exercises_with_component_phases = user_possible_exercises_with_user_exercise_info(user_id)

    # List of Dictionary Construction
    return construct_available_exercises_list(exercises_with_component_phases)
