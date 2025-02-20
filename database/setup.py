# File: database/setup.py
from .base import Base, engine

def init_db():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(bind=engine)

def drop_db():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)