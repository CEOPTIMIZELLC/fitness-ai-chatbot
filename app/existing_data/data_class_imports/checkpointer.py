from app import db
from flask import current_app, abort
from langgraph.checkpoint.postgres import PostgresSaver

def setup_checkpointer():
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        try:
            with db.session.begin():  # Start a transaction with automatic commit/rollback
                checkpointer.setup()
        except Exception as e:
            abort(400, description=f"Error setting up checkpoint: {e}")
        db.session.commit()
