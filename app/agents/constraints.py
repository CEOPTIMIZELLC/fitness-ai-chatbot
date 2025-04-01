
# Links each entry and item with the "used" variables, determining if item j is the item at entry i.
def link_entry_and_item(model, items, entry_vars, number_of_entries, used_vars):
    for i in range(number_of_entries):
        for j in range(len(items)):
            # Ensures that if an item is chosen (used_vars[i][j] is True), then:
            # The corresponding entry_vars[i] must match the index j.
            model.Add(entry_vars[i] == j).OnlyEnforceIf(used_vars[i][j])
            model.Add(entry_vars[i] != j).OnlyEnforceIf(used_vars[i][j].Not())
    return model

# Define and create a list of variables to determine if an entry is active.
# As well, this will constrain the possible items that an inactive entry can have to be an invalid one.
def constrain_active_entries_vars(model, entry_vars, number_of_entries, duration_vars, active_entry_vars):
    # Ensure that deactivation is done from the back to the front.
    for i in range(number_of_entries - 1):
        # A entry must be active if the entry ahead of it is active.
        model.Add(active_entry_vars[i] >= active_entry_vars[i + 1])
    
    # Add constraints to deactivated items.
    for i in range(number_of_entries):
        # If a item is active, it will have a valid item type. Otherwise, it will be given an invalid item type.
        model.Add(entry_vars[i] >= 1).OnlyEnforceIf(active_entry_vars[i])
        model.Add(entry_vars[i] == 0).OnlyEnforceIf(active_entry_vars[i].Not())

        # If a item is active, then its duration MUST be greater than 0. Otherwise it is 0.
        model.Add(duration_vars[i] >= 0).OnlyEnforceIf(active_entry_vars[i])
        model.Add(duration_vars[i] == 0).OnlyEnforceIf(active_entry_vars[i].Not())
    
    return model

# Constraint: The duration of a item may only be a value between the minimum and maximum values allowed.
def entry_within_min_max(model, items, minimum_key, maximum_key, number_of_entries, used_vars, duration_vars):
    for i in range(number_of_entries):
        for j, item in enumerate(items):
            # The duration_vars[i] must be within the allowed range.
            model.Add(duration_vars[i] >= item[minimum_key]).OnlyEnforceIf(used_vars[i][j])
            model.Add(duration_vars[i] <= item[maximum_key]).OnlyEnforceIf(used_vars[i][j])
    return model

# For each entry, add a constraint stating that it can't be the same item as the next entry.
def no_consecutive_identical_items(model, entry_vars, number_of_entries):
    for i in range(number_of_entries - 1):
        model.Add(entry_vars[i] != entry_vars[i + 1])
    return model

# For each entry, add a constraint stating that it can't be the same item as the next entry.
# Ensure that only active entries are considered in this.
def no_consecutive_identical_active_items(model, entry_vars, number_of_entries, active_entry_vars):
    # For each entry in the macrocycle make sure that the entry at the current index isn't the same as the mesocyle at the next index.
    for i in range(number_of_entries - 1):
        (
            model.Add(entry_vars[i] != entry_vars[i + 1])       # Current entry and next entry may not be the same.
            .OnlyEnforceIf(
                active_entry_vars[i],                           # Current entry must be active.
                active_entry_vars[i + 1])                       # Next entry must be active.
        )

    return model

# Adds constraint ensuring that, at least once within an 'n' frame window, the desired item must be at an entry.
def no_n_items_without_desired_item(model, allowed_n, desired_item_index, entry_vars, number_of_entries):
    # The following is a sliding window of allowed_n items that ensures that at least one will be stabilization endurance.
    for i in range(number_of_entries - (allowed_n - 1)):  # Ensure we have a window of allowed_n
        # Boolean variables for the window, indicating whether item j in the allowed_n item window is stabilization endurance.
        desired_item_in_window = [
            model.NewBoolVar(f'desired_item_{j}') 
            for j in range(i, i + allowed_n)]
        
        # For each item in the window
        for j, item_is_desired_item in zip(range(i, i + allowed_n), desired_item_in_window):
            # Ensures that, if the item in the window is stabilization endurance:
            # then the entry at the corresponding index will be set to stabilization endurance.
            model.Add(entry_vars[j] == desired_item_index).OnlyEnforceIf(item_is_desired_item)
            model.Add(entry_vars[j] != desired_item_index).OnlyEnforceIf(item_is_desired_item.Not())
        
        # Ensures that at least one of the items in the window will be stabilization endurance.
        model.AddBoolOr(desired_item_in_window)
    return model

# Adds constraint ensuring that, at least once within an 'n' frame window, the desired item must be at an entry.
# This is only done for active entries.
def no_n_active_items_without_desired_item(model, allowed_n, desired_item_index, entry_vars, number_of_entries, active_entry_vars):
    # The following is a sliding window of allowed_n items that ensures that at least one will be stabilization endurance.
    for i in range(number_of_entries - (allowed_n -1)):  # Ensure we have a window of allowed_n
        # Boolean variables for the window, indicating whether item j in the allowed_n item window is stabilization endurance.
        active_window = [
            active_entry_vars[j]
            for j in range(i, i + allowed_n)]
        desired_item_in_window = [
            model.NewBoolVar(f'desired_item_{j}') 
            for j in range(i, i + allowed_n)]
        
        # For each item in the window
        for j, item_is_desired_item, item_is_active in zip(range(i, i + allowed_n), desired_item_in_window, active_window):
            # Ensures that, if the item in the window is stabilization endurance:
            # then the entry at the corresponding index will be set to stabilization endurance.
            model.Add(entry_vars[j] == desired_item_index).OnlyEnforceIf(item_is_desired_item, item_is_active)
            model.Add(entry_vars[j] != desired_item_index).OnlyEnforceIf(item_is_desired_item.Not())
        
        # Ensures that at least one of the items in the window will be stabilization endurance.
        model.AddBoolOr(desired_item_in_window)
    return model

# Ensures that only required entrys will be used at any entry in the entry_set.
def only_use_required_items(model, required_items, entry_vars):
    # Ensures that only required items will be used at any entry in the macrocycle.
    for entry in entry_vars:
        model.AddAllowedAssignments([entry], [(item,) for item in required_items])
    return model

# Ensures that each required entry occurs at least once in the entry_set.
def use_all_required_items(model, required_items, entry_vars, number_of_entries):
    for item_index in required_items:
        # Create an array of Boolean variables indicating whether this item appears in each entry
        item_in_entries = [
            model.NewBoolVar(f'item_{item_index}_in_entry_{i}') 
            for i in range(number_of_entries)]
        
        for i in range(number_of_entries):
            model.Add(entry_vars[i] == item_index).OnlyEnforceIf(item_in_entries[i])
            model.Add(entry_vars[i] != item_index).OnlyEnforceIf(item_in_entries[i].Not())

        # Ensure that at least one of these Boolean variables is true
        model.AddBoolOr(item_in_entries)
    return model


def constrain_active_entry(model, entry, activator, min_if_active=0, max_if_active=1, value_if_inactive=0):
    # Enforce entry = 0 if the activator is off.
    model.Add(entry == value_if_inactive).OnlyEnforceIf(activator.Not())

    # Enforce min <= entry <= max if the activator is on
    model.Add(entry >= min_if_active).OnlyEnforceIf(activator)
    model.Add(entry <= max_if_active).OnlyEnforceIf(activator)
    return model


# Method for the creation of what is essentially an optional variable. 
# This was created to reduce repetition of code
def create_optional_intvar(model, name_of_entry_var, activator, min_if_active=0, max_if_active=1, value_if_inactive=0):
    var_entry = model.NewIntVar(value_if_inactive, max_if_active, name_of_entry_var)
    model = constrain_active_entry(model, entry=var_entry, activator=activator, 
                                   min_if_active=min_if_active, max_if_active=max_if_active, 
                                   value_if_inactive=value_if_inactive)
    return model, var_entry


# Create an intvar for an optional spread variable to try for later minimization.
def create_spread_intvar(model, entry_vars, entry_var_name, active_entry_vars, max_value_allowed):
    min_entry_var = model.NewIntVar(0, max_value_allowed, f"min_{entry_var_name}")
    max_entry_var = model.NewIntVar(0, max_value_allowed, f"max_{entry_var_name}")

    # Ensure min_entry_var <= all entry_vars
    # Ensure max_exercise_var >= all entry_vars
    for entry_vars_i, active_entry_vars_i in zip(entry_vars, active_entry_vars):
        for entry_var_j, active_entry_vars_j in zip(entry_vars_i, active_entry_vars_i):
            model.Add(min_entry_var <= entry_var_j).OnlyEnforceIf(active_entry_vars_j)
            model.Add(max_entry_var >= entry_var_j).OnlyEnforceIf(active_entry_vars_j)

    # Minimize the spread
    spread_var = model.NewIntVar(0, max_value_allowed, f"{entry_var_name}_spread")
    model.Add(spread_var == max_entry_var - min_entry_var)
    return model, spread_var







# Constraint: The duration of a day may only be a number of hours between the allowed time.
def day_duration_within_availability(model, duration_vars, availability):
    # Each day
    for duration_vars_for_day, availability_for_day in zip(duration_vars, availability):
        # Ensure total time does not exceed the macrocycle_allowed_weeks
        model.Add(sum(duration_vars_for_day) <= availability_for_day)
    return model

# Constraint: Force all phase components required in every workout to be included at least once.
def use_workout_required_components(model, required_phase_components, active_phase_components, active_workday_vars):
    # Each required phase component
    for required_component_index in required_phase_components:
        # Each day
        for active_phase_component, active_workday in zip(active_phase_components, active_workday_vars):
            # Set the active indicator for the phase to active on each active day
            model.Add(active_phase_component[required_component_index] == True).OnlyEnforceIf(active_workday)
    return model

# Constraint: Force all phase components required in every microcycle to be included at least once.
def use_microcycle_required_components(model, required_phase_components, active_phase_components):
    # Each required phase component
    for required_component_index in required_phase_components:
        active_window = []
        # Each day
        for active_phase_component in active_phase_components:
            # Add the corresponding indicator for phase component activity to the list to be checked
            active_window.append(active_phase_component[required_component_index])
        model.AddBoolOr(active_window)
    return model

# Constraint: # Force number of occurrences of a phase component within in a microcycle to be within number allowed.
def frequency_within_min_max(model, phase_components, active_phase_components, min_key, max_key):
    # Boolean variables indicating whether the phase component has been used at least once in the microcycle
    used_phase_components = [
        model.NewBoolVar(f'phase_component_{i}_is_active') 
        for i in range(len(phase_components))]

    # Each required phase component
    for phase_component_index, phase_component in enumerate(phase_components):
        active_window = []

        # Each day
        for active_phase_component in active_phase_components:
            # Add the corresponding indicator for phase component activity to the list to be checked
            active_window.append(active_phase_component[phase_component_index])

        # Ensure that the phase component has been used more than once
        model.Add(sum(active_window) == 0).OnlyEnforceIf(used_phase_components[phase_component_index].Not())

        # Constrain to be between the minimum and maximum allowed (if one exists)
        if phase_component[min_key]:
            model.Add(sum(active_window) >= phase_component[min_key]).OnlyEnforceIf(used_phase_components[phase_component_index])
        if phase_component[max_key]:
            model.Add(sum(active_window) <= phase_component[max_key]).OnlyEnforceIf(used_phase_components[phase_component_index])
    return model

# Constraint: Every bodypart division must be done consecutively for a phase component.
def consecutive_bodyparts_for_component(model, phase_components, active_phase_components):
    # Retrieve the list of all unique phase component ids.
    unique_components = list(set(phase_component["id"] for phase_component in phase_components))
    for unique_component in unique_components:
        # Find all phase components with the same id.
        required_phase_components = [i for i, phase_component in enumerate(phase_components) if phase_component["id"] == unique_component]
        # Each day
        for active_phase_component in active_phase_components:
            # Retrieve the corresponding indicator for all phase components of the same type on a day.
            required_phase_components_for_day = [active_phase_component[i] for i in required_phase_components]
            if required_phase_components_for_day:
                # Ensure all variables in required_phase_components_for_day are equal (either all 1 or all 0)
                first_var = required_phase_components_for_day[0]
                for var in required_phase_components_for_day[1:]:
                    model.Add(var == first_var)
    return model


# Constraint: The numer of exercises may only be a number of exercises between the minimum and maximum exercises per bodypart allowed.
def exercises_per_bodypart_within_min_max(model, items, minimum_key, maximum_key, used_vars):
    # Each required phase component
    for i, item in enumerate(items[1:], start=1):
        # Retrieve the count for every exercise of the phase type.
        exercises_of_phase = [exercise_phases[i] for exercise_phases in used_vars]

        # Constrain to be between the minimum and maximum allowed (if one exists)
        if item[minimum_key]:
            model.Add(sum(exercises_of_phase) >= item[minimum_key])
        if item[maximum_key]:
            model.Add(sum(exercises_of_phase) <= item[maximum_key])
    return model

# Due to inability to make an expression as a constraint in a single line, a few steps must be taken prior.
# This method performs the in between steps and returns the final duration variable.
# total_set_duration = (seconds_per_exercise*(1+.1*basestrain)* rep_count + rest_time) * set_count
def create_duration_var(model, i, workout_length, seconds_per_exercise, reps, rest, sets):
    # Create the entry for phase component's duration
    # duration = (seconds_per_exercise * rep_count + rest_time) * set_count
    duration_var_entry = model.NewIntVar(0, workout_length, f'duration_{i}')

    # Temporary variable for seconds per exercise and the rep count. (seconds_per_exercise * rep_count)
    seconds_per_exercise_and_reps = model.NewIntVar(0, workout_length, f'seconds_per_exercise_and_rep_count_{i}')
    
    model.AddMultiplicationEquality(seconds_per_exercise_and_reps, [seconds_per_exercise, reps])

    # Temporary variable for the previous product and the rest time. (seconds_per_exercise * rep_count + rest_time)
    duration_with_rest = model.NewIntVar(0, workout_length, f'duration_with_rest_{i}')

    # In between step for added components.
    model.Add(duration_with_rest == seconds_per_exercise_and_reps + (5 * rest))

    # Completed constraint.
    model.AddMultiplicationEquality(duration_var_entry, [duration_with_rest, sets])
    return model, duration_var_entry