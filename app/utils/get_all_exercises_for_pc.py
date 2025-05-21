from config import verbose

def get_exercises_for_pc_conditions(exercises, phase_component, conditions=[]):
    return [i for i, exercise in enumerate(exercises, start=1) 
            if all(f(exercise, phase_component) for f in conditions)]

def get_exercises_for_pc(exercises, phase_component):
    conditions = [lambda exercise, phase_component: phase_component["pc_ids"] in exercise["pc_ids"],
                  # lambda exercise, phase_component: phase_component["component_id"] in exercise["component_ids"],
                  # lambda exercise, phase_component: phase_component["subcomponent_id"] in exercise["subcomponent_ids"],
                  lambda exercise, phase_component: (1 in exercise["bodypart_ids"]) or (phase_component["bodypart_id"] in exercise["bodypart_ids"])]

    exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, conditions)

    message = None
    pc_name = f"'{phase_component['phase_name']}' '{phase_component['component_name']}' '{phase_component['subcomponent_name']}'"

    if (exercises_for_pc == []) and (phase_component["bodypart_id"] == 1):
        message = f"{pc_name} has no true exercises for bodypart '{phase_component['bodypart_name']}'. If total body, include all exercises for this component phase."
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, conditions[0:1])

    if exercises_for_pc == []:
        message = f"{pc_name} still has no exercises for bodypart '{phase_component['bodypart_name']}'."

    if message and verbose:
        print(message)
    return exercises_for_pc

# A method for retrieving the possible exercises for all phase components.
# This method removes exercises specific for a phase commponent from those that are allowed for a phase component without any true exercises.
def get_exercises_for_all_pcs(exercises, phase_components):
    number_of_possible_exercises = len(exercises)

    exercises_for_pcs = [
        get_exercises_for_pc(exercises, phase_component)
        for phase_component in phase_components
    ]

    # All phase components that have every possible exercise applied to them.
    pc_indices_without_true_exercises = [
        i
        for i in range(len(exercises_for_pcs))
        if len(exercises_for_pcs[i]) == number_of_possible_exercises
    ]

    # Remove the exercises from the phase components without true exercises for minimum searching.
    for i in pc_indices_without_true_exercises:
        # Compare to every other list of exercises that have true exercises.
        for j in range(len(exercises_for_pcs)):
            if j in pc_indices_without_true_exercises:
                continue
            exercises_for_pcs[i] = list(set(exercises_for_pcs[i]) - set(exercises_for_pcs[j]))

    return exercises_for_pcs
