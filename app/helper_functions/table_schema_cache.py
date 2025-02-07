from sqlalchemy import inspect

import json

def get_foreign_keys(inspector, table_name):
    foreign_keys_map = {}
    for fk in inspector.get_foreign_keys(table_name):
        for column, referred_column in zip(fk["constrained_columns"], fk["referred_columns"]):
            foreign_keys_map[column] = f"{fk['referred_table']}.{referred_column}"
    return foreign_keys_map

def get_database_schema(db):
    """Uses Inspector to get the current schema of the database and converts it to a readable text format."""
    inspector = inspect(db.engine)
    schema = ""
    for table_name in inspector.get_table_names():
        schema += f"Table: {table_name}\n"

        # Get primary and foreign keys
        primary_keys = set(inspector.get_pk_constraint(table_name)["constrained_columns"])
        foreign_keys_map = get_foreign_keys(inspector=inspector, table_name=table_name)
        
        for column in inspector.get_columns(table_name):
            col_name = column["name"]
            col_type = str(column["type"])

            # Check for primary key
            if col_name in primary_keys:
                col_type += ", Primary Key"

            # Check for foreign key
            if col_name in foreign_keys_map:
                col_type += f", Foreign Key to {foreign_keys_map[col_name]}"

            # Check for if the column is nullable.
            if column["nullable"]:
                col_type += ", Nullable"
            else:
                col_type += ", Not Nullable"

            # Check for if autoincremented.
            if column["autoincrement"]:
                col_type += ", Autoincrements"

            # Check for default value.
            elif column["default"]:
                col_type += f", Default value of {str(column["default"])}"

            schema += f"- {col_name}: {col_type}\n"
        schema += "\n"
    print("Retrieved database schema.")
    return schema
