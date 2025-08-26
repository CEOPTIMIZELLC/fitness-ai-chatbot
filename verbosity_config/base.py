# Logging configurations options for the database initialization.
class DatabaseInitVerbosityConfigBase:
    verbose = True
    introductions = True
    clustering = True
    data_errors = True

# Logging configurations options for the routes.
class RouteVerbosityConfigBase:
    verbose = True

# Logging configurations options for the main agent.
class MainAgentVerbosityConfigBase:
    verbose = True
    agent_introductions = True
    agent_steps = False
    agent_output = False
    input_info = False
    system_message = False
    formatted_schedule = True

# Logging configurations options for the main sub agents.
class MainSubAgentVerbosityConfigBase:
    verbose = True
    agent_introductions = True
    agent_steps = False
    agent_output = False
    input_info = False
    system_message = False
    parsed_goal = False
    formatted_schedule = False

# Logging configurations options for the solver preprocessing verbosity.
class SchedulerPreProcessingVerbosityConfigBase:
    verbose = False
    exercises_for_pc_steps = False

# Logging configurations options for the solver agent verbosity.
class SchedulerVerbosityConfigBase:
    verbose = False
    agent_time = False
    agent_steps = False
    agent_output = False
    formatted_schedule = False

# Logging configurations for general application.
class VerbosityConfigBase:
    verbose = True
    DatabaseInit = DatabaseInitVerbosityConfigBase
    Route = RouteVerbosityConfigBase
    MainAgent = MainAgentVerbosityConfigBase
    MainSubAgent = MainSubAgentVerbosityConfigBase
    SchedulerPreProcessing = SchedulerPreProcessingVerbosityConfigBase
    Scheduler = SchedulerVerbosityConfigBase
