from ortools.sat.python import cp_model

def optimize_goal_time():
    model = cp_model.CpModel()
    
    # Phases and their properties
    phases = ['a', 'b', 'c', 'd', 'e']
    min_durations = {'a': 4, 'b': 3, 'c': 3, 'd': 4, 'e': 2}
    max_durations = {'a': 6, 'b': 7, 'c': 5, 'd': 4, 'e': 6}
    is_goal = {'a': True, 'b': False, 'c': False, 'd': True, 'e': False}
    is_required = {'a': True, 'b': True, 'c': False, 'd': True, 'e': True}
    macrocycle_allowed_weeks = 43
    
    # Upper bound on number of phases (greedy estimation)
    num_mesocycles = macrocycle_allowed_weeks // min(min_durations.values())
    
    # Variables
    mesocycle_vars = [
        model.NewIntVar(0, len(phases) - 1, f'phase_{i}') 
        for i in range(num_mesocycles)]
    
    duration_vars = [
        model.NewIntVar(0, macrocycle_allowed_weeks, f'duration_{i}') 
        for i in range(num_mesocycles)]
    
    used_vars = [
        [
            model.NewBoolVar(f'phase_{i}_is_{j}') 
            for j in range(len(phases))
        ] 
        for i in range(num_mesocycles)]
    
    goal_time_terms = []
    
    # Ensure durations fit within phase limits
    for i in range(num_mesocycles):
        for j, phase in enumerate(phases):
            model.Add(mesocycle_vars[i] == j).OnlyEnforceIf(used_vars[i][j])
            model.Add(duration_vars[i] >= min_durations[phase]).OnlyEnforceIf(used_vars[i][j])
            model.Add(duration_vars[i] <= max_durations[phase]).OnlyEnforceIf(used_vars[i][j])
    
    # Ensure total time does not exceed the macrocycle_allowed_weeks
    model.Add(sum(duration_vars) <= macrocycle_allowed_weeks)
    
    # Ensure required phases are used at least once
    for j, phase in enumerate(phases):
        if is_required[phase]:
            model.Add(sum(used_vars[i][j] for i in range(num_mesocycles)) >= 1)
    
    # Define goal time calculation
    goal_time = model.NewIntVar(0, macrocycle_allowed_weeks, 'goal_time')
    for i in range(num_mesocycles):
        for j, phase in enumerate(phases):
            if is_goal[phase]:
                goal_contrib = model.NewIntVar(0, macrocycle_allowed_weeks, f'goal_contrib_{i}_{j}')
                model.AddMultiplicationEquality(goal_contrib, [duration_vars[i], used_vars[i][j]])
                goal_time_terms.append(goal_contrib)
    model.Add(goal_time == sum(goal_time_terms))
    
    # Maximize goal time
    model.Maximize(goal_time)
    
    # Solve the problem
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        schedule = []
        total_time = 0
        for i in range(num_mesocycles):
            phase_index = solver.Value(mesocycle_vars[i])
            duration = solver.Value(duration_vars[i])
            if duration > 0:
                schedule.append((phases[phase_index], duration))
                total_time += duration
        
        print(f"Total Scheduled Time: {total_time}/{macrocycle_allowed_weeks}")
        print(f"Total Goal Time: {solver.Value(goal_time)}")
        print("Schedule:")
        for phase, duration in schedule:
            print(f"Phase {phase} for {duration} units")
    else:
        print("No feasible solution found.")

# Run optimization
optimize_goal_time()
