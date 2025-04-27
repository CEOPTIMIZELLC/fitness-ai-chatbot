import os
import sys
import psycopg2
import load_env_var
#from load_env_var import pgBase

# Make sure database exists.
def create_initial_db():
    conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user=os.environ["POSTRGRES_USER"],
            password=os.environ["POSTRGRES_PASSWORD"])
    conn.autocommit = True

    # Open a cursor to perform database operations.
    cur = conn.cursor()

    # Reset Database if indicated to
    cur.execute(f"DROP DATABASE IF EXISTS {os.environ["postrgres_database"]}")
    
    # Create a new database if one doesn"t.
    cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{os.environ["postrgres_database"]}'")
    exists = cur.fetchone()
    if not exists:
        cur.execute(f"CREATE DATABASE {os.environ["postrgres_database"]}")
    
    conn.commit()
    cur.close()

create_initial_db()


