
# Integer variable representing the metric for the phase component chosen at exercise i.
def intvar_list_from_phase_components(model, ids, phase_components, name_of_metric, min_key, max_key):
    return [
        model.NewIntVar(phase_components[pc_index][min_key], 
                        phase_components[pc_index][max_key], 
                        f'{name_of_metric}_{i}') 
        for i, pc_index in enumerate(ids)]

# Integer variable representing the metric chosen at element i.
def intvar_list_from_elements(model, number_of_elements, name_of_metric, min_value, max_value):
    return [
        model.NewIntVar(min_value, 
                        max_value, 
                        f'{name_of_metric}_{i}') 
        for i in range(number_of_elements)]

# Links each entry and item with the "used" variables, determining if item j is the item at entry i.
def link_entry_and_item(model, items, entry_vars, number_of_entries, used_vars):
    for i in range(number_of_entries):
        for j in range(len(items)):
            # Ensures that if an item is chosen (used_vars[i][j] is True), then:
            # The corresponding entry_vars[i] must match the index j.
            model.Add(entry_vars[i] == j).OnlyEnforceIf(used_vars[i][j])
            model.Add(entry_vars[i] != j).OnlyEnforceIf(used_vars[i][j].Not())
    return None

def constrain_active_entry(model, entry, activator, min_if_active=0, max_if_active=1, value_if_inactive=0):
    # Enforce entry = 0 if the activator is off.
    model.Add(entry == value_if_inactive).OnlyEnforceIf(activator.Not())

    # Enforce min <= entry <= max if the activator is on
    model.Add(entry >= min_if_active).OnlyEnforceIf(activator)
    model.Add(entry <= max_if_active).OnlyEnforceIf(activator)

    return None

# Method for the creation of what is essentially an optional variable. 
# This was created to reduce repetition of code
def create_optional_intvar(model, name_of_entry_var, activator, min_if_active=0, max_if_active=1, value_if_inactive=0):
    var_entry = model.NewIntVar(value_if_inactive, max_if_active, name_of_entry_var)
    model = constrain_active_entry(model, entry=var_entry, activator=activator, 
                                   min_if_active=min_if_active, max_if_active=max_if_active, 
                                   value_if_inactive=value_if_inactive)
    return var_entry

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
    return spread_var

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
    
    return None

def entry_equals(model, var, item, key, condition=None):
    """Generic function to add equals constraints with optional condition."""
    if (key in item) and (item[key] is not None):
        constraint = model.Add(var == item[key])
        if condition is not None:
            constraint.OnlyEnforceIf(condition)

# Constraint: The duration of a item may only be the value allowed.
def entries_equal(model, items, key, number_of_entries, used_vars, duration_vars):
    for i in range(number_of_entries):
        for j, item in enumerate(items):
            # The duration_vars[i] must be within the allowed range of the item.
            entry_equals(
                model, duration_vars[i], item,
                key, used_vars[i][j]
            )
    return None

def entry_within_min_max(model, var, item, min_key, max_key, condition=None):
    """Generic function to add min/max constraints with optional condition."""
    if (min_key in item) and (item[min_key] is not None):
        constraint = model.Add(var >= item[min_key])
        if condition is not None:
            constraint.OnlyEnforceIf(condition)
    if (max_key in item) and (item[max_key] is not None):
        constraint = model.Add(var <= item[max_key])
        if condition is not None:
            constraint.OnlyEnforceIf(condition)

# Constraint: The duration of a item may only be a value between the minimum and maximum values allowed.
def entries_within_min_max(model, items, minimum_key, maximum_key, number_of_entries, used_vars, duration_vars):
    for i in range(number_of_entries):
        for j, item in enumerate(items):
            # The duration_vars[i] must be within the allowed range of the item.
            entry_within_min_max(
                model, duration_vars[i], item,
                minimum_key, maximum_key, used_vars[i][j]
            )
    return None

# Constraint: # Force number of occurrences of a phase component within in a microcycle to be within number allowed.
def frequency_within_min_max(model, phase_components, active_phase_components, minimum_key, maximum_key):
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
        entry_within_min_max(
            model, sum(active_window), phase_component,
            minimum_key, maximum_key,
            used_phase_components[phase_component_index]
        )
    return None

# Constraint: The number of exercises may only be a number of exercises between the minimum and maximum exercises per bodypart allowed.
def exercises_per_bodypart_within_min_max(model, required_items, items, minimum_key, maximum_key, used_vars):
    for item_index in required_items:
        exercises_of_phase = [row[item_index] for row in used_vars]

        # Constrain to be between the minimum and maximum allowed (if one exists)
        entry_within_min_max(
            model, sum(exercises_of_phase), items[item_index],
            minimum_key, maximum_key
        )
    return None

# Adds constraint ensuring that, at least once within an 'n' frame window, the desired item must be at an entry.
def no_n_items_without_desired_item(model, allowed_n, desired_item_index, entry_vars, number_of_entries, active_entry_vars=None):
    # The following is a sliding window of allowed_n items that ensures that at least one will be stabilization endurance.
    for i in range(number_of_entries - (allowed_n - 1)):  # Ensure we have a window of allowed_n
        # Boolean variables for the window, indicating whether item j in the allowed_n item window is stabilization endurance.
        desired_item_in_window = [
            model.NewBoolVar(f'desired_item_{j}') 
            for j in range(i, i + allowed_n)]
        
        # For each item in the window
        for j, item_is_desired_item in zip(range(i, i + allowed_n), desired_item_in_window):
            # If active_entry_vars is provided, then only enforce if the entry is active.
            if active_entry_vars:
                (model.Add(entry_vars[j] == desired_item_index)
                 .OnlyEnforceIf(item_is_desired_item, active_entry_vars[j]))
            else:
                (model.Add(entry_vars[j] == desired_item_index)
                 .OnlyEnforceIf(item_is_desired_item))

            (model.Add(entry_vars[j] != desired_item_index)
             .OnlyEnforceIf(item_is_desired_item.Not()))
        
        # Ensures that at least one of the items in the window will be stabilization endurance.
        model.AddBoolOr(desired_item_in_window)
    return None

# For each entry, add a constraint stating that it can't be the same item as the next entry.
def no_consecutive_identical_items(model, entry_vars, active_entry_vars=None):
    """Prevents consecutive identical items in active entries."""
    for i in range(len(entry_vars) - 1):
        constraint = model.Add(entry_vars[i] != entry_vars[i + 1])
        if active_entry_vars:
            constraint.OnlyEnforceIf(active_entry_vars[i], active_entry_vars[i + 1])
    return None

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
    return None

# Ensures that only required entrys will be used at any entry in the entry_set.
def only_use_required_items(model, required_items, entry_vars, active_entry_vars=None, conditions=None):
    # Ensures that only required items will be used at any entry in the macrocycle.
    for i, entry in enumerate(entry_vars):
        constraint = model.AddAllowedAssignments([entry], [(item,) for item in required_items])
        condition = []
        if conditions is not None:
            condition.append(conditions[i])
        if active_entry_vars is not None:
            condition.append(active_entry_vars[i])
        if condition != []:
            constraint.OnlyEnforceIf(condition)
    return None

# Ensures that each required entry occurs at least once in the entry_set.
def use_all_required_items(model, required_items, used_vars, soft_constraint=False):
    soft_conditions=[]
    for item_index in required_items:
        conditions = [row[item_index] for row in used_vars]
        constraint = model.AddBoolOr(conditions)
        if soft_constraint:
            conditions_not_met = [condition.Not() for condition in conditions]
            condition_met = model.NewBoolVar(f"{item_index}_occurs_once")

            # If the phase component is selected at any point, condition_met should be True
            constraint.OnlyEnforceIf(condition_met)
            model.AddBoolAnd(conditions_not_met).OnlyEnforceIf(condition_met.Not())

            soft_conditions.append(condition_met)
    return soft_conditions

# Ensures that an item only occurs once in the entry_set.
def no_repeated_items(model, required_items, used_vars):
    for item_index in required_items:
        conditions = [row[item_index] for row in used_vars]
        model.Add(sum(conditions) <= 1)
    return None

# Constraint: Force all phase components required in every workout to be included at least once.
def use_workout_required_components(model, required_items, used_vars, active_entry_vars):
    # Each required phase component
    for item_index in required_items:
        # Each day
        for row, active_entry in zip(used_vars, active_entry_vars):
            # Set the active indicator for the phase to active on each active day
            model.Add(row[item_index] == True).OnlyEnforceIf(active_entry)
    return None

# Constraint: The duration of a day may only be a number of hours between the allowed time.
def day_duration_within_availability(model, duration_vars, availability):
    # Each day
    for duration_vars_for_day, availability_for_day in zip(duration_vars, availability):
        # Ensure total time does not exceed the macrocycle_allowed_weeks
        model.Add(sum(duration_vars_for_day) <= availability_for_day)
    return None

def symmetry_breaking_constraints(model, entry_vars, active_vars):
    """Add symmetry breaking constraints to reduce search space."""
    # Force active exercises to be ordered
    for i in range(len(active_vars) - 1):
        # If exercise i+1 is active, exercise i must be active
        model.Add(active_vars[i] >= active_vars[i + 1])
        
        # If both exercises are active, force ordering of phase components
        model.Add(entry_vars[i] <= entry_vars[i + 1]).OnlyEnforceIf([
            active_vars[i], active_vars[i + 1]
        ])
    return None

def add_tight_bounds(model, entry_vars, used_vars, items, name="", minimum_key=None, maximum_key=None):
    """Add tight bounds to variables to help the solver."""
    # Track used phase components
    phase_component_counts = {}
    
    # Calculate minimum and maximum possible counts for each phase component
    for i, item in enumerate(items):
        min_count = item.get(minimum_key, 0) or 0
        max_count = item.get(maximum_key, len(entry_vars)) or len(entry_vars)
        
        # Create counter variable with tight bounds
        counter = model.NewIntVar(min_count, max_count, f'{name}_counter_{i}')
        model.Add(counter == sum(row[i] for row in used_vars))
        phase_component_counts[i] = counter
        
    return phase_component_counts

def retrieve_indication_of_increase(model, items, max_performance, var_index, performance_var, used_item):
    # Booleans to check if the performance increased for whichever item was selected.
    performance_increase_for_pc_met = [model.NewBoolVar(f'item_{i}_performance_increase_for_{var_index}')
                                       for i in range(1, len(items))]

    # Boolean to check if a performance increase occurred for the phase component.
    performance_penalty = model.NewIntVar(0, max_performance // 100, f'performance_penalty_for_{var_index}')
    performance_difference = model.NewIntVar(0, max_performance, f'performance_difference_for_{var_index}')

    for (performance_increase_met_for_item, item, item_selected) in zip(performance_increase_for_pc_met[1:], items[1:], used_item[1:]):

        # Ensure the check is off if the item isn't picked.
        model.Add(performance_increase_met_for_item == 0).OnlyEnforceIf(item_selected.Not())

        # If the maximum is going to be reached, do not exceed it.
        model.Add(performance_var > item["performance"]).OnlyEnforceIf(item_selected, performance_increase_met_for_item)
        model.Add(performance_var <= item["performance"]).OnlyEnforceIf(item_selected, performance_increase_met_for_item.Not())

        # Calculate penalty if increase isn't met.
        model.Add(performance_difference == 0).OnlyEnforceIf(item_selected, performance_increase_met_for_item)
        model.Add(performance_difference == (100 + item["performance"] - performance_var)).OnlyEnforceIf(item_selected, performance_increase_met_for_item.Not())

    model.AddDivisionEquality(performance_penalty, performance_difference, 100)
    return performance_penalty
