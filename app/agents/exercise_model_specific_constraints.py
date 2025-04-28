
# Due to inability to make an expression as a constraint in a single line, a few steps must be taken prior.
# This method performs the in between steps and returns the final duration variable.
# total_set_duration = (seconds_per_exercise * rep_count + rest_time) * set_count
def create_duration_var(model, i, max_duration=0, seconds_per_exercise=0, reps=0, sets=0, rest=0, name=""):
    if name != "":
        name += "_"

    # Create the entry for phase component's duration
    # duration = (seconds_per_exercise * rep_count + rest_time) * set_count
    duration_var_entry = model.NewIntVar(0, max_duration, f'{name}duration_{i}')

    # Temporary variable for seconds per exercise and the rep count. (seconds_per_exercise * rep_count)
    seconds_per_exercise_and_reps = model.NewIntVar(0, max_duration, f'{name}seconds_per_exercise_and_rep_count_{i}')
    model.AddMultiplicationEquality(seconds_per_exercise_and_reps, [seconds_per_exercise, reps])

    # Temporary variable for the previous product and the rest time. (seconds_per_exercise * rep_count + rest_time)
    duration_with_rest = model.NewIntVar(0, max_duration, f'{name}duration_with_rest_{i}')

    # In between step for added components.
    model.Add(duration_with_rest == seconds_per_exercise_and_reps + (5 * rest))

    # Completed constraint.
    model.AddMultiplicationEquality(duration_var_entry, [duration_with_rest, sets])
    return duration_var_entry


# In between step for intensity and base strain.
def _is_intensity(model, i, name="", scaled=1, max_duration=0, intensity=None, base_strain=None):
    scaled_intensity_value = 0
    intensity_name = ""
    scaled_count = 1

    if intensity != None:
        scaled_intensity_value += intensity
        intensity_name += "intensity_"
        scaled_count += 1

    if base_strain != None:
        scaled_intensity_value += base_strain
        intensity_name += "base_strain_"
        scaled_count += 1

    # If either were encountered, scale the intensity.
    if scaled_count > 1:
        scaled = 10 * scaled
        scaled_intensity_value += scaled
        scaled_intensity = model.NewIntVar(0, scaled * max_duration, f'{name}scaled_{intensity_name}{i}')
        model.Add(scaled_intensity == (scaled_intensity_value))
        return scaled_intensity
    else:
        return 1

# Due to inability to make an expression as a constraint in a single line, a few steps must be taken prior.
# This method performs the in between steps and returns the final duration variable.
# total_set_duration = (seconds_per_exercise * (1 + .1 * basestrain) * rep_count + rest_time) * set_count
# total_set_duration = (seconds_per_exercise * (10 + basestrain) * rep_count + 10 * rest_time) * set_count
def create_exercise_effort_var(model, i, max_duration=0, seconds_per_exercise=0, reps=0, sets=0, rest=0, intensity=None, base_strain=None, name="", scaled=1):
    if name != "":
        name += "_"

    # In between step for base strain.
    scaled_base_strain = _is_intensity(model, i, name, scaled, max_duration, intensity, base_strain)

    # Create the entry for phase component's duration
    # duration = (seconds_per_exercise * rep_count + rest_time) * set_count
    effort_var_entry = model.NewIntVar(0, scaled * max_duration, f'{name}effort_{i}')

    # Temporary variable for seconds per exercise and the rep count. (seconds_per_exercise * rep_count)
    seconds_per_exercise_and_reps = model.NewIntVar(0, scaled * max_duration, f'{name}seconds_per_exercise_and_rep_count_{i}')
    model.AddMultiplicationEquality(seconds_per_exercise_and_reps, [seconds_per_exercise, scaled_base_strain, reps])

    # Temporary variable for the previous product and the rest time. (seconds_per_exercise * rep_count + rest_time)
    effort_with_rest = model.NewIntVar(0, scaled * max_duration, f'{name}effort_with_rest_{i}')

    # In between step for added components.
    model.Add(effort_with_rest == seconds_per_exercise_and_reps + (5 * scaled * rest))

    # Completed constraint.
    model.AddMultiplicationEquality(effort_var_entry, [effort_with_rest, sets])
    return effort_var_entry


# Indicate that an exercise chosen is weighted if the exercise is a weighted exercise.
def constrain_weighted_exercises_var(model, used_exercise_vars, weighted_exercise_vars, weighted_exercise_indices):
    for used_exercise_var, weighted_exercise_var in zip(used_exercise_vars, weighted_exercise_vars):
        weighted_exercise_used = [used_exercise_var[i] for i in weighted_exercise_indices]
        weighted_exercise_not_used = [used_exercise_var[i].Not() for i in weighted_exercise_indices]

        # If any weighted exercise is selected, has_weighted_exercise should be True
        model.AddBoolOr(weighted_exercise_used).OnlyEnforceIf(weighted_exercise_var)
        model.AddBoolAnd(weighted_exercise_not_used).OnlyEnforceIf(weighted_exercise_var.Not())
    return None

# Only allow intensity if a weighted exercise is selected. Otherwise, intensity is 0.
def constrain_intensity_vars(model, intensity_vars, phase_component_ids, phase_components, weighted_exercise_vars):
    # For each exercise position
    for intensity_var, pc_index, has_weighted_exercise in zip(intensity_vars, phase_component_ids, weighted_exercise_vars):
        # Get minimum intensity for this phase component (default to 1 if not specified)
        min_intensity = phase_components[pc_index]["intensity_min"] or 1
        
        # Constrain intensity based on weighted exercise selection
        model.Add(intensity_var >= min_intensity).OnlyEnforceIf(has_weighted_exercise)
        model.Add(intensity_var == 0).OnlyEnforceIf(has_weighted_exercise.Not())
    return None

def constrain_training_weight_vars(model, intensity_vars, exercises, training_weight_vars, used_exercise_vars, weighted_exercise_vars):
    # Link the exercise variables and the training weight variables by ensuring the training weight is equal to the one rep max * intensity for the exercise chose at exercise i.
    for intensity_var, training_weight_var, used_exercise_var, has_weighted_exercise in zip(intensity_vars, training_weight_vars, used_exercise_vars, weighted_exercise_vars):
        
        # Training weight is 0 if no weighted exercise is selected
        model.Add(training_weight_var == 0).OnlyEnforceIf(has_weighted_exercise.Not())
        for exercise, exercise_for_exercise_var in zip(exercises, used_exercise_var[1:]):
            model.Add(training_weight_var == (exercise["one_rep_max"] * intensity_var)).OnlyEnforceIf(exercise_for_exercise_var, has_weighted_exercise)
    return None

def constrain_volume_vars(model, volume_vars, max_volume, reps_vars, sets_vars, training_weight_vars, weighted_exercise_vars):
    # Link the exercise variables and the volume variables by ensuring the volume is equal to the reps * sets * training weight for the exercise chose at exercise i.
    for i, (reps_var, sets_var, training_weight_var, volume_var, has_weighted_exercise) in enumerate(zip(reps_vars, sets_vars, training_weight_vars, volume_vars, weighted_exercise_vars)):
        volume_var_if_unloaded = model.NewIntVar(0, max_volume, f'temp_volume_{i}_unloaded')
        model.AddMultiplicationEquality(volume_var_if_unloaded, [reps_var, sets_var, 100 * 100])

        volume_var_if_loaded = model.NewIntVar(0, max_volume, f'temp_volume_{i}_loaded')
        model.AddMultiplicationEquality(volume_var_if_loaded, [reps_var, sets_var, training_weight_var])

        model.Add(volume_var == volume_var_if_loaded).OnlyEnforceIf(has_weighted_exercise)
        model.Add(volume_var == volume_var_if_unloaded).OnlyEnforceIf(has_weighted_exercise.Not())
    return None

def constrain_density_vars(model, density_vars, duration_vars, working_duration_vars, max_duration):
    # Link the exercise variables and the density variables by ensuring the density is equal to the duration / working duration for the exercise chose at exercise i.
    for i, (duration_var, working_duration_var, density_var) in enumerate(zip(duration_vars, working_duration_vars, density_vars)):
        # Create a boolean variable to track if working_duration is 0
        base_duration_is_0 = model.NewBoolVar(f'base_duration_{i}_is_0')
        
        # Create an intermediate variable that will be 1 when working_duration is 0 and will be working_duration otherwise
        non_zero_base_duration_var = model.NewIntVar(1, max_duration, 'non_zero_base_duration_{i}')
        
        # Link the conditions
        model.Add(non_zero_base_duration_var == 1).OnlyEnforceIf(base_duration_is_0)
        model.Add(non_zero_base_duration_var == duration_var).OnlyEnforceIf(base_duration_is_0.Not())
        model.Add(duration_var == 0).OnlyEnforceIf(base_duration_is_0)
        model.Add(duration_var > 0).OnlyEnforceIf(base_duration_is_0.Not())
        
        # Now we can safely do the division (scaled up by 100 to avoid floating point)
        model.AddDivisionEquality(density_var, 100 * working_duration_var, non_zero_base_duration_var)
        
        # Set density to 0 when working_duration is 0
        model.Add(density_var == 0).OnlyEnforceIf(base_duration_is_0)
    return None

def constrain_performance_vars(model, performance_vars, volume_vars, density_vars):
    for volume_var, density_var, performance_var in zip(volume_vars, density_vars, performance_vars):
        model.AddMultiplicationEquality(performance_var, [volume_var, density_var])
    return None