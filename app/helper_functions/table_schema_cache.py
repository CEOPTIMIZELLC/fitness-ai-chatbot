from sqlalchemy import inspect

import json

# Retrieves all of the information about the schema for each column in a table.
def retrieve_schema_info(columns):
    return [
        {
            "name": col["name"], 
            "type": str(col["type"]), 
            "nullable": col["nullable"], 
            "comment": col["comment"]
        }
        for col in columns
    ]

# Retrieves all foreign key columns and what they are referencing for a table.
def retrieve_foreign_keys(fks):
    return [
        {
            "column": fk["constrained_columns"], 
            "references": fk["referred_table"]
        }
        for fk in fks
    ]

# Stringify the json formatted information.
def stringify_schema(schema_info):
    schema_text = ""
    for table, columns in schema_info.items():
        schema_text += f"Table: {table}\n"
        for col in columns:
            schema_text += f"  - {col['name']} ({col['type']}) {'[NULLABLE]' if col['nullable'] else ''}\n"
        schema_text += "\n"
    return schema_text

# Retrieve the names of every table in the database.
def retrieve_table_schema(db):
    inspector = inspect(db.engine)  # Create an inspector bound to the engine

    tables = inspector.get_table_names()

    schema_info = {}
    foreign_keys = {}

    for table in tables:
        columns = inspector.get_columns(table)
        schema_info[table] = retrieve_schema_info(columns)

        fks = inspector.get_foreign_keys(table)
        foreign_keys[table] = retrieve_foreign_keys(fks)
        
    schema_text = stringify_schema(schema_info)
    
    return {"schema_info": schema_info, "foreign_keys": foreign_keys, "schema_text": schema_text}


def get_database_schema(db):
    inspector = inspect(db.engine)
    schema = ""
    for table_name in inspector.get_table_names():
        schema += f"Table: {table_name}\n"

        # Get primary keys
        primary_keys = set(inspector.get_pk_constraint(table_name)["constrained_columns"])

        # Get foreign keys
        foreign_keys_map = {}
        for fk in inspector.get_foreign_keys(table_name):
            for column, referred_column in zip(fk["constrained_columns"], fk["referred_columns"]):
                foreign_keys_map[column] = f"{fk['referred_table']}.{referred_column}"
        
        for column in inspector.get_columns(table_name):
            col_name = column["name"]
            col_type = str(column["type"])

            # Check for primary key
            if col_name in primary_keys:
                col_type += ", Primary Key"

            # Check for foreign key
            if col_name in foreign_keys_map:
                col_type += f", Foreign Key to {foreign_keys_map[col_name]}"

            schema += f"- {col_name}: {col_type}\n"
        schema += "\n"
    print("Retrieved database schema.")
    return schema