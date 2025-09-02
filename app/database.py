import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime

Base = declarative_base()

# Ensure directory exists
db_folder = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(db_folder, exist_ok=True)

DATABASE_PATH = os.path.join(db_folder, "flights.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Arrival(Base):
    __tablename__ = 'arrivals'
    id = Column(Integer, primary_key=True)
    airline = Column(String(100))
    flight = Column(String(50))
    origin = Column(String(100))
    status = Column(String(50))
    scheduled_time = Column(String(20))
    actual_time = Column(String(20))
    gate = Column(String(20))
    scrape_timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Departure(Base):
    __tablename__ = 'departures'
    id = Column(Integer, primary_key=True)
    airline = Column(String(100))
    flight = Column(String(50))
    origin = Column(String(100))
    status = Column(String(50))
    scheduled_time = Column(String(20))
    actual_time = Column(String(20))
    gate = Column(String(20))
    scrape_timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()

