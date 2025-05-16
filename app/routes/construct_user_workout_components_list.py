dummy_phase_component = {
    "id": 0,
    "workout_component_id": 0,
    "workout_day_id": 0,
    "bodypart_id": 0,
    "bodypart_name": "Inactive",
    "duration": 0,
    "phase_component_id": 0,
    "phase_id": 0,
    "phase_name": "Inactive",
    "component_id": 0,
    "component_name": "Inactive",
    "subcomponent_id": 0,
    "subcomponent_name": "Inactive",
    "pc_ids": 0,
    "density_priority": 0,
    "volume_priority": 0,
    "load_priority": 0,
    "name": "Inactive",
    "reps_min": 0, 
    "reps_max": 0,
    "sets_min": 0,
    "sets_max": 0,
    "tempo": 0,
    "seconds_per_exercise": 0,
    "intensity_min": 0,
    "intensity_max": 0,
    "rest_min": 0,                          # Adjusted so that rest is a multiple of 5.
    "rest_max": 0,                          # Adjusted so that rest is a multiple of 5.
    "duration_min": 0,
    "duration_min_desired": 0,
    "duration_min_max": 0,
    "duration_max": 0,
    "working_duration_min": 0,
    "working_duration_max": 0,
    "volume_min": 0,
    "volume_max": 0,
    "density_min": 0,              # Scaled up to avoid floating point errors from model.
    "density_max": 0,              # Scaled up to avoid floating point errors from model.
    "exercises_per_bodypart_workout_min": 0,
    "exercises_per_bodypart_workout_max": 0,
    "exercise_selection_note": 0,
    'allowed_exercises': [0],
}

def user_component_dict(workout, pc):
    """Format the user workout component data."""
    return {
        "workout_component_id": workout.id,
        "workout_day_id": workout.workout_day_id,
        "bodypart_id": workout.bodypart_id,
        "bodypart_name": workout.bodyparts.name,
        "duration": workout.duration,
        "phase_component_id": pc.id,
        "phase_id": pc.phase_id,
        "phase_name": pc.phases.name,
        "component_id": pc.component_id,
        "component_name": pc.components.name,
        "subcomponent_id": pc.subcomponent_id,
        "subcomponent_name": pc.subcomponents.name,
        "pc_ids": [pc.component_id, pc.subcomponent_id],
        "density_priority": pc.subcomponents.density,
        "volume_priority": pc.subcomponents.volume,
        "load_priority": pc.subcomponents.load,
        "name": pc.name,
        "reps_min": pc.reps_min, "reps_max": pc.reps_max,
        "sets_min": pc.sets_min,
        "sets_max": pc.sets_max,
        "tempo": pc.tempo,
        "seconds_per_exercise": pc.seconds_per_exercise,
        "intensity_min": pc.intensity_min,
        "intensity_max": pc.intensity_max or 100,
        "rest_min": pc.rest_min // 5,                          # Adjusted so that rest is a multiple of 5.
        "rest_max": pc.rest_max // 5,                          # Adjusted so that rest is a multiple of 5.
        "duration_min": pc.duration_min,
        "duration_min_desired": pc.duration_min,
        "duration_min_max": pc.duration_min,
        "duration_max": pc.duration_max,
        "working_duration_min": pc.working_duration_min,
        "working_duration_max": pc.working_duration_max,
        "volume_min": pc.volume_min,
        "volume_max": pc.volume_max,
        "density_min": int(pc.density_min * 100),              # Scaled up to avoid floating point errors from model.
        "density_max": int(pc.density_max * 100),              # Scaled up to avoid floating point errors from model.
        "exercises_per_bodypart_workout_min": pc.exercises_per_bodypart_workout_min if pc.exercises_per_bodypart_workout_min != None else 1,
        "exercises_per_bodypart_workout_max": pc.exercises_per_bodypart_workout_max,
        "exercise_selection_note": pc.exercise_selection_note,
    }


def construct_user_workout_components_list(user_workout_components):
    user_workout_components_list = [dummy_phase_component]

    # Convert the query into a list of dictionaries, adding the information for the phase restrictions.
    for user_workout_component in user_workout_components:
        user_workout_components_list.append(user_component_dict(user_workout_component, user_workout_component.phase_components))
    return user_workout_components_list
