import os
import sys
import psycopg2
import load_env_var
#from load_env_var import pgBase

# Make sure database exists.
def create_initial_db():
    # Connect to the default database.
    conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user=os.environ["POSTRGRES_USER"],
            password=os.environ["POSTRGRES_PASSWORD"])
    conn.autocommit = True

    # Open a cursor to perform database operations.
    cur = conn.cursor()

    # Check if the database exists.
    cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{os.environ["postrgres_database"]}'")
    exists = cur.fetchone()
    if exists: 
        print("Current instance of the database exists. Deleting old instance.")
    else:
        print("No current instance of the database exists.")

    # Reset Database if indicated to
    # cur.execute(f"DROP DATABASE IF EXISTS {os.environ["postrgres_database"]}")
    cur.execute(f"DROP DATABASE IF EXISTS {os.environ["postrgres_database"]} WITH (FORCE)")
    
    # Create a new database if one doesn"t.
    cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{os.environ["postrgres_database"]}'")
    exists = cur.fetchone()
    if not exists:
        print("Creating new database.")
        cur.execute(f"CREATE DATABASE {os.environ["postrgres_database"]}")
    
    conn.commit()
    cur.close()

create_initial_db()


