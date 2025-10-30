from datetime import timedelta, datetime

# Helper method for type conversion where applicable.
def get_value_and_convert(my_dict, key, type_cast, default_value=None):
    value = my_dict.get(key)

    if value != None:
        return type_cast(value)
    return default_value

def convert_value_and_alter(my_dict, key, type_cast, default_value=None):
    if default_value:
        converted_value = get_value_and_convert(my_dict, key, type_cast, default_value)
    else:
        converted_value = get_value_and_convert(my_dict, key, type_cast)
    
    if converted_value != None:
        my_dict[key] = converted_value
    
    return None


# Helper method for timedelta conversion where applicable.
def get_value_and_convert_to_timedelta(my_dict, key, default_value=None):
    value = my_dict.get(key)

    if value != None:
        return timedelta(seconds=value)
    return default_value

def convert_value_and_alter_to_timedelta(my_dict, key, default_value=None):
    if default_value:
        converted_value = get_value_and_convert_to_timedelta(my_dict, key, default_value)
    else:
        converted_value = get_value_and_convert_to_timedelta(my_dict, key)
    
    if converted_value != None:
        my_dict[key] = converted_value
    
    return None


# Helper method for date conversion where applicable.
def get_value_and_convert_to_date(my_dict, key, default_value=None):
    value = my_dict.get(key)

    if value != None:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return default_value

def convert_value_and_alter_to_date(my_dict, key, default_value=None):
    if default_value:
        converted_value = get_value_and_convert_to_date(my_dict, key, default_value)
    else:
        converted_value = get_value_and_convert_to_date(my_dict, key)
    
    if converted_value != None:
        my_dict[key] = converted_value
    
    return None



