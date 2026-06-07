# backend/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

# Abhi local testing ke liye SQLite use kar rahe hain, production pr ye PostgreSQL URL ban jayega
SQLALCHEMY_DATABASE_URL = "sqlite:///./hotel.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1. Rooms Table
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(Integer, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False)  # Standard, Deluxe, Suite
    price_per_night = Column(Float, nullable=False)
    status = Column(String, default="Available")  # Available, Booked, Maintenance

    bookings = relationship("Booking", back_populates="room")

# 2. Bookings Table
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String, nullable=False)
    guest_email = Column(String, nullable=True)
    guest_phone = Column(String, nullable=True)
    cnic_passport = Column(String, nullable=True)
    
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    total_bill = Column(Float, nullable=False)
    
    # HITL (Human-in-the-loop) ke liye status 'Draft' hoga jab AI banaye ga, 
    # Admin ke confirm karne pr 'Confirmed' ho jayega.
    booking_status = Column(String, default="Draft")  # Draft, Confirmed, Cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    room = relationship("Room", back_populates="bookings")

# Database initialization function
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()