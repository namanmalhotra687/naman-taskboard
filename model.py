from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database Configuration
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Item Model
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    description = Column(String(250))
    status = Column(String(20))
    deadline = Column(Date)
    is_generated = Column(Boolean, default=False)
    generated_at = Column(DateTime, default=None)
    category = Column(String(50), default="Other")
    tag = Column(String(50), default="General")

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)