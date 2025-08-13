from datetime import timedelta, date, datetime

# Recursively go through dictionary to change time deltas
# Correct time delta for serializing for JSON output.
def recursively_change_dict_timedeltas(my_data_structure):
    # If the value is a timedelta, make it into a string.
    if (isinstance(my_data_structure, timedelta) 
        or isinstance(my_data_structure, date) 
        or isinstance(my_data_structure, datetime)):
        my_data_structure = str(my_data_structure)

    # If a dictionary, go through and change all of my items.
    elif isinstance(my_data_structure, dict):
        for key, value in my_data_structure.items():
            my_data_structure[key] = recursively_change_dict_timedeltas(value)
    
    # If a list, go through the list and check each item.
    elif isinstance(my_data_structure, list):
        for i, item in enumerate(my_data_structure):
            my_data_structure[i] = recursively_change_dict_timedeltas(item)

    return my_data_structure