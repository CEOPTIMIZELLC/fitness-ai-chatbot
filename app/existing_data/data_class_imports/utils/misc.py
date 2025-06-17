import re
from app import db

def set_keys_to_lowercase(d):
    return {k.lower(): v for k, v in d.items()}

def create_list_of_table_entries(ids, names, model_type):
    # Create list of Components
    for i, name in enumerate(names, start=1):
        ids[name] = i
        db_entry = model_type(id=i, name=name)

        # Using merge to handle duplicates gracefully
        db.session.merge(db_entry)
    db.session.commit()
    return ids

# Function to determine the connector for new column value
def determine_connector(text):
    if ' & ' in text:
        return 'and'
    elif ' | ' in text:
        return 'or'
    else:
        return None

# Function to extract the number or set it to 1
def extract_number(text):
    # Search for a number inside parentheses at the end of the string
    match = re.search(r"\((\d+)\)$", text)
    if match:
        return int(match.group(1))  # Return the number inside parentheses
    else:
        return 1  # Return 1 if no number is found
