from ortools.sat.python import cp_model

def optimize_goal_time():
    model = cp_model.CpModel()
    
    # States and their properties
    states = ['a', 'b', 'c', 'd', 'e']
    min_durations = {'a': 4, 'b': 3, 'c': 3, 'd': 4, 'e': 2}
    max_durations = {'a': 6, 'b': 7, 'c': 5, 'd': 4, 'e': 6}
    is_goal = {'a': True, 'b': False, 'c': False, 'd': True, 'e': False}
    is_required = {'a': True, 'b': True, 'c': False, 'd': True, 'e': True}
    timespan = 43
    
    # Upper bound on number of states (greedy estimation)
    max_segments = timespan // min(min_durations.values())
    
    # Variables
    state_vars = [
        model.NewIntVar(0, len(states) - 1, f'state_{i}') 
        for i in range(max_segments)]
    
    duration_vars = [
        model.NewIntVar(0, timespan, f'duration_{i}') 
        for i in range(max_segments)]
    
    used_vars = [
        [
            model.NewBoolVar(f'state_{i}_is_{j}') 
            for j in range(len(states))
        ] 
        for i in range(max_segments)]
    
    goal_time_terms = []
    
    # Ensure durations fit within state limits
    for i in range(max_segments):
        for j, state in enumerate(states):
            model.Add(state_vars[i] == j).OnlyEnforceIf(used_vars[i][j])
            model.Add(duration_vars[i] >= min_durations[state]).OnlyEnforceIf(used_vars[i][j])
            model.Add(duration_vars[i] <= max_durations[state]).OnlyEnforceIf(used_vars[i][j])
    
    # Ensure total time does not exceed the timespan
    model.Add(sum(duration_vars) <= timespan)
    
    # Ensure required states are used at least once
    for j, state in enumerate(states):
        if is_required[state]:
            model.Add(sum(used_vars[i][j] for i in range(max_segments)) >= 1)
    
    # Define goal time calculation
    goal_time = model.NewIntVar(0, timespan, 'goal_time')
    for i in range(max_segments):
        for j, state in enumerate(states):
            if is_goal[state]:
                goal_contrib = model.NewIntVar(0, timespan, f'goal_contrib_{i}_{j}')
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
        for i in range(max_segments):
            state_index = solver.Value(state_vars[i])
            duration = solver.Value(duration_vars[i])
            if duration > 0:
                schedule.append((states[state_index], duration))
                total_time += duration
        
        print(f"Total Scheduled Time: {total_time}/{timespan}")
        print(f"Total Goal Time: {solver.Value(goal_time)}")
        print("Schedule:")
        for state, duration in schedule:
            print(f"State {state} for {duration} units")
    else:
        print("No feasible solution found.")

# Run optimization
optimize_goal_time()
