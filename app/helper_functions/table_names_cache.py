from .. import db
from sqlalchemy import inspect

# Retrieve the names of every table in the database.
def retrieve_table_names():
    inspector = inspect(db.engine)  # Create an inspector bound to the engine
    return inspector.get_table_names()