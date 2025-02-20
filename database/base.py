# database/base.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database connection details from environment variables
DB_USER = os.getenv("POSTGRES_USER", "anas")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "A1n9a8s9")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "aiaas")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(bind=engine)

def drop_db():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)