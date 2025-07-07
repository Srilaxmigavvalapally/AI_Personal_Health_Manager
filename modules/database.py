# modules/database.py

import datetime
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, 
                        ForeignKey, Text, Float)
from sqlalchemy.orm import declarative_base, sessionmaker

# --- DATABASE SETUP ---
DATABASE_URL = "sqlite:///./health_manager.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DATABASE MODELS (TABLES) ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    email = Column(String, unique=True)

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    dosage = Column(String)
    schedule = Column(String)
    start_date = Column(DateTime)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    storage_key = Column(String, unique=True, nullable=False)
    description = Column(String)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    doctor_name = Column(String, index=True)
    specialty = Column(String)
    appointment_datetime = Column(DateTime, nullable=False)
    location = Column(String)
    notes = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
class HealthVital(Base):
    __tablename__ = "health_vitals"
    id = Column(Integer, primary_key=True, index=True)
    vital_type = Column(String, index=True, nullable=False)
    value1 = Column(Float, nullable=False)
    value2 = Column(Float, nullable=True)
    unit = Column(String)
    record_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

# --- UTILITY FUNCTION TO CREATE TABLES ---
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)