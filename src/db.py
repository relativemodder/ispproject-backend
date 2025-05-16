from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine
from sqlalchemy import event
import os

Base = declarative_base()

class Database:
    def __init__(self, db_url: str = None):
        # Default to SQLite file database if no URL provided
        if db_url is None:
            db_url = "sqlite:///./app.db"
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Enable foreign key support for SQLite
        if "sqlite" in db_url:
            @event.listens_for(Engine, "connect")
            def _set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    def get_session(self):
        return self.SessionLocal()

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
