# app/db_session.py
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from app import db  # your Flask-SQLAlchemy object

# independent Session factory bound to the same engine
SessionLocal = sessionmaker(bind=db.engine, future=True, expire_on_commit=False)

@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
