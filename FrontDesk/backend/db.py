# backend/db.py
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# import os
# from .models import Base

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./helpdesk.db")
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# def init_db():
#     Base.metadata.create_all(bind=engine)


# backend/db.py
from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./frontdesk.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

def init_db():
    # create database tables
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)


