from app.models import Phase_Library, Phase_Component_Library, Phase_Component_Bodyparts

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_possible_phase_components(phase_id):
    # Retrieve all possible phase components that can be selected.
    possible_phase_components = (
        Phase_Component_Library.query
        .join(Phase_Library)
        .filter(Phase_Library.id == phase_id)
        .order_by(Phase_Component_Library.id.asc())
        .all()
    )
    return possible_phase_components

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_phase_component_bodyparts(phase_id):
    # Retrieve all possible phase components that can be selected.
    possible_phase_component_bodyparts = (
        Phase_Component_Bodyparts.query
        .filter(Phase_Component_Bodyparts.phase_id == phase_id)
        .order_by(Phase_Component_Bodyparts.id.asc())
        .all()
    )
    return possible_phase_component_bodyparts    

def phase_component_dict(pc, bodypart_id, bodypart_name, required_within_microcycle):
    """Format the phase component data."""
    return {
        "id": pc.id,
        "phase_component_id": pc.id,
        "name": pc.name,
        "phase_id": pc.phase_id,
        "phase_name": pc.phases.name,
        "component_id": pc.component_id,
        "component_name": pc.components.name,
        "subcomponent_id": pc.subcomponent_id,
        "subcomponent_name": pc.subcomponents.name,
        "pc_ids": [pc.component_id, pc.subcomponent_id],
        "required_every_workout": pc.required_every_workout,
        "required_within_microcycle": required_within_microcycle,
        "frequency_per_microcycle_min": pc.frequency_per_microcycle_min,
        "frequency_per_microcycle_max": pc.frequency_per_microcycle_max,
        "intensity_min": pc.intensity_min,
        "intensity_max": pc.intensity_max or 100,
        "exercises_per_bodypart_workout_min": pc.exercises_per_bodypart_workout_min if pc.exercises_per_bodypart_workout_min != None else 1,
        "exercises_per_bodypart_workout_max": pc.exercises_per_bodypart_workout_max if pc.exercises_per_bodypart_workout_max != None else 1,
        # "duration_min": ((pc.exercises_per_bodypart_workout_min or 1) * pc.duration_min),
        # "duration_max": ((pc.exercises_per_bodypart_workout_max or 1) * pc.duration_max),
        "duration_min": pc.duration_min,
        "duration_max": pc.duration_max,
        "duration_min_desired": pc.duration_min,
        "duration_min_max": pc.duration_min,
        "bodypart_id": bodypart_id, 
        "bodypart": bodypart_name, 
        "bodypart_name": bodypart_name
    }

# Using the information for the phase components, generate the phase components with the minimum and maximum possible values.
def construct_phase_component_list(possible_phase_components, possible_phase_component_bodyparts):
    possible_phase_components_list = []

    # Convert the query into a list of dictionaries.
    for possible_phase_component in possible_phase_components:
        # If the phase component is resistance, append it multiple times.
        if possible_phase_component.component_id == 6:
            for pc_bodypart in possible_phase_component_bodyparts:
                possible_phase_components_list.append(phase_component_dict(possible_phase_component, pc_bodypart.bodypart_id, pc_bodypart.bodyparts.name, pc_bodypart.required_within_microcycle))
        # Append only once for full body if any other phase component.
        else:
            possible_phase_components_list.append(phase_component_dict(possible_phase_component, 1, "total_body", possible_phase_component.required_within_microcycle))
    
    return possible_phase_components_list

def Main(phase_id):
    # Retrieve all possible phase component body parts.
    possible_phase_component_bodyparts = retrieve_phase_component_bodyparts(phase_id)

    # Retrieve all possible phase components that can be selected for the phase id.
    possible_phase_components = retrieve_possible_phase_components(phase_id)
    return construct_phase_component_list(possible_phase_components, possible_phase_component_bodyparts)